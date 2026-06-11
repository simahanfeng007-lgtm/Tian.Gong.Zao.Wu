from __future__ import annotations

"""L6.73.8 launcher consistency verifier."""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

CURRENT_VERSION = "L6.73.8"
MANIFEST_REL = Path("scripts/launcher_manifest_l67220.json")
GENERATOR_MARKER = "GENERATED_BY=L6.73.8 LauncherTemplateGenerator"
VERSION_RE = re.compile(r"L6\.\d+\.\d+")


class CheckFailure(RuntimeError):
    pass


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_manifest(root: Path) -> dict[str, Any]:
    path = root / MANIFEST_REL
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def fail(errors: list[str], rel: str, msg: str) -> None:
    errors.append(f"{rel}: {msg}")


def ensure_posix_executable(path: Path) -> bool:
    """Restore executable bits lost by Python zipfile.extractall."""
    try:
        mode = path.stat().st_mode
        if mode & 0o111:
            return True
        os.chmod(path, mode | 0o755)
        return bool(path.stat().st_mode & 0o111)
    except OSError:
        return False


def is_crlf_only(data: bytes) -> bool:
    return b"\r\n" in data and b"\n" not in data.replace(b"\r\n", b"")


def is_lf_only(data: bytes) -> bool:
    return b"\r\n" not in data and b"\r" not in data and b"\n" in data


def bash_path_candidates(path: Path) -> list[str]:
    resolved = path.resolve()
    candidates = [str(resolved)]
    if os.name == "nt" and resolved.drive:
        posix = resolved.as_posix()
        drive = resolved.drive.rstrip(":").lower()
        rest = posix.split(":/", 1)[1] if ":/" in posix else posix.lstrip("/")
        candidates.extend([f"/mnt/{drive}/{rest}", f"/{drive}/{rest}", posix])
    deduped: list[str] = []
    for candidate in candidates:
        if candidate not in deduped:
            deduped.append(candidate)
    return deduped


def check_common(root: Path, entry: dict[str, Any], data: bytes, text: str, errors: list[str]) -> None:
    rel = entry["output_path"]
    if GENERATOR_MARKER not in text:
        fail(errors, rel, "missing generator marker")
    versions = set(VERSION_RE.findall(text))
    if versions != {CURRENT_VERSION}:
        fail(errors, rel, f"version drift: {sorted(versions)}")
    for forbidden in ("L6.72.5", "L6.72.10"):
        if forbidden in text:
            fail(errors, rel, f"forbidden old display version: {forbidden}")
    if "TIANGONG_ROOT_HINT" in text:
        fail(errors, rel, "TIANGONG_ROOT_HINT must not be written by launcher")
    if "monkey" in text.lower():
        fail(errors, rel, "monkey patch wording detected")
    if re.search(r"\bv1\b", text, flags=re.I):
        fail(errors, rel, "v1 import/reference wording detected")
    if re.search(r"while\s+true|nohup|setsid|start\s+/b", text, flags=re.I):
        fail(errors, rel, "background loop/process pattern detected")


def check_windows(root: Path, entry: dict[str, Any], data: bytes, errors: list[str]) -> None:
    rel = entry["output_path"]
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as exc:
        fail(errors, rel, f"BAT is not ASCII: {exc}")
        text = data.decode("utf-8", errors="replace")
    if not is_crlf_only(data):
        fail(errors, rel, "BAT must use CRLF only")
    check_common(root, entry, data, text, errors)
    lower = text.lower()
    if "python -c" in lower or re.search(r"py\s+-3(?:\.\d+)?\s+-c", lower):
        fail(errors, rel, "inline python -c probe detected")
    if "python_probe_l67217.py" not in lower:
        fail(errors, rel, "PYTHON_PROBE_L67217.py is required")
    if "title %title%" not in lower:
        fail(errors, rel, "title command missing")
    if "enabledelayedexpansion" in lower:
        fail(errors, rel, "EnableDelayedExpansion must not be used")
    if "disableDelayedExpansion".lower() not in lower:
        fail(errors, rel, "DisableDelayedExpansion missing")
    if "set \"linyuanzhe_root_hint=%root%\"" not in lower:
        fail(errors, rel, "LINYUANZHE_ROOT_HINT assignment missing")
    if "%*" in text:
        fail(errors, rel, "user argument passthrough %* is forbidden")
    if "scan_common" not in lower or "walk_up" not in lower or "try_root" not in lower:
        fail(errors, rel, "shared root-finding semantics missing")


def check_posix(root: Path, entry: dict[str, Any], data: bytes, errors: list[str]) -> None:
    rel = entry["output_path"]
    text = data.decode("utf-8", errors="replace")
    if not is_lf_only(data):
        fail(errors, rel, "SH/COMMAND must use LF only")
    check_common(root, entry, data, text, errors)
    if not os.access(root / rel, os.X_OK):
        if not ensure_posix_executable(root / rel):
            fail(errors, rel, "POSIX launcher must be executable")
    for required in ("BASH_VERSION", "BASH_SOURCE", "PYTHON_BIN", "validate_python_bin", "nullglob", "LINYUANZHE_ROOT_HINT", "scan_common", "walk_up"):
        if required not in text:
            fail(errors, rel, f"required shell guard missing: {required}")
    forbidden_tokens = ("curl ", "wget ", "Invoke-WebRequest", "http://", "https://")
    for token in forbidden_tokens:
        if token in text:
            fail(errors, rel, f"remote download/http token forbidden in launcher: {token.strip()}")
    if "$@" in text:
        fail(errors, rel, "user argument passthrough $@ is forbidden")
    bash_errors: list[str] = []
    for candidate in bash_path_candidates(root / rel):
        result = subprocess.run(["bash", "-n", candidate], cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        if result.returncode == 0:
            return
        bash_errors.append(result.stderr.strip() or result.stdout.strip() or f"exit={result.returncode}")
    fail(errors, rel, "bash -n failed: " + " | ".join(bash_errors[-3:]))


def verify(root: Path) -> tuple[list[str], list[str]]:
    manifest = load_manifest(root)
    errors: list[str] = []
    rows: list[str] = []
    if manifest.get("version") != CURRENT_VERSION:
        errors.append(f"manifest version drift: {manifest.get('version')!r}")
    seen: set[str] = set()
    for entry in manifest.get("entries", []):
        rel = entry["output_path"]
        if rel in seen:
            fail(errors, rel, "duplicate output path in manifest")
            continue
        seen.add(rel)
        path = root / rel
        if not path.exists():
            fail(errors, rel, "missing generated launcher")
            continue
        data = path.read_bytes()
        if entry["platform"] == "windows":
            check_windows(root, entry, data, errors)
        else:
            if not (path.stat().st_mode & 0o111):
                ensure_posix_executable(path)
            check_posix(root, entry, data, errors)
        rows.append(f"PASS  {entry['platform']:<7}  {entry['entry_kind']:<22}  {rel}")
    return rows, errors


def main() -> int:
    p = argparse.ArgumentParser(description="Verify L6.73.8 generated launchers.")
    p.add_argument("--root", default=str(project_root()))
    args = p.parse_args()
    root = Path(args.root).resolve()
    rows, errors = verify(root)
    for row in rows:
        print(row)
    if errors:
        print("[L6.73.8] launcher verification FAILED", file=sys.stderr)
        for e in errors:
            print("FAIL  " + e, file=sys.stderr)
        return 1
    print(f"[L6.73.8] launcher verification PASS: {len(rows)} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
