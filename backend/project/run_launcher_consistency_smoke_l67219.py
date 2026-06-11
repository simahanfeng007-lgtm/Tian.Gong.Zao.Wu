from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

BAD_CONTROL = set(range(0, 9)) | {11, 12} | set(range(14, 32))
BROKEN_PATTERNS = (
    ".linyuanzhective_assets",
    "scriptsalidate_demo_package.py",
    "scripts\\nalidate_demo_package.py",
    "backend/backend/project",
    "backend\\backend\\project",
)


def _normalized_text(text: str) -> str:
    return re.sub(r"/+", "/", text.replace("\\", "/"))


def _is_crlf_only(data: bytes) -> bool:
    return b"\r\n" in data and b"\n" not in data.replace(b"\r\n", b"")


def _is_lf_only(data: bytes) -> bool:
    return b"\r\n" not in data and b"\r" not in data and b"\n" in data


def _bash_path_candidates(path: Path) -> list[str]:
    resolved = path.resolve()
    candidates = [str(resolved)]
    if sys.platform.startswith("win") and resolved.drive:
        posix = resolved.as_posix()
        drive = resolved.drive.rstrip(":").lower()
        rest = posix.split(":/", 1)[1] if ":/" in posix else posix.lstrip("/")
        candidates.extend([f"/mnt/{drive}/{rest}", f"/{drive}/{rest}", posix])
    deduped: list[str] = []
    for candidate in candidates:
        if candidate not in deduped:
            deduped.append(candidate)
    return deduped


def _all_wrappers(root: Path) -> list[Path]:
    return sorted(
        [
            p
            for p in list(root.rglob("*.bat")) + list(root.rglob("*.sh")) + list(root.rglob("*.command"))
            if p.is_file() and not any(part in {".git", "__pycache__"} for part in p.parts)
        ],
        key=lambda p: p.relative_to(root).as_posix(),
    )


def _check_critical_launcher_semantics(root: Path) -> list[str]:
    errors: list[str] = []
    critical_expectations = {
        "backend/launchers/run_prompt_trace_smoke_l67214.sh": [
            'cd "$(dirname "$0")/../project"',
            "python3 -S -B run_prompt_trace_smoke_l67214.py",
            "TIANGONG_PROMPT_TRACE_FILE",
            "TIANGONG_PROMPT_TUNER_FILE",
            "PYTHONDONTWRITEBYTECODE=1",
        ],
        "backend/launchers/run_prompt_trace_smoke_l67214.bat": [
            'cd /d "%~dp0../project"',
            "python -S -B run_prompt_trace_smoke_l67214.py",
            "TIANGONG_PROMPT_TRACE_FILE",
            "TIANGONG_PROMPT_TUNER_FILE",
            "PYTHONDONTWRITEBYTECODE=1",
        ],
        "launchers/run_workmode_activation_check_l6718.sh": [
            'cd "$ROOT/backend/project"',
            "run_no_pyc_compile_check_l6738.py",
            "TIANGONG_PROMPT_TRACE_FILE",
            "TIANGONG_PROMPT_TUNER_FILE",
            "python -S -B run_agent.py",
        ],
        "launchers/run_workmode_activation_check_l6718.bat": [
            'cd /d "%~dp0../backend/project"',
            "run_no_pyc_compile_check_l6738.py",
            "TIANGONG_PROMPT_TRACE_FILE",
            "TIANGONG_PROMPT_TUNER_FILE",
            '"%PYTHON_EXE%" -S -B run_agent.py',
        ],
        "frontend/linyuanzhe_frontend/run_desktop_demo.sh": [
            'PYTHON_BIN="${PYTHON_BIN:-python3}"',
            'PYTHONDONTWRITEBYTECODE=1 "$PYTHON_BIN" -S -B run_desktop_demo.py',
        ],
        "frontend/linyuanzhe_frontend/run_desktop_demo.bat": [
            '"%PYTHON_EXE%" -S -B run_desktop_demo.py',
        ],
    }
    for rel, required_tokens in critical_expectations.items():
        path = root / rel
        if not path.exists():
            errors.append(f"{rel}: missing critical launcher")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        norm = _normalized_text(text)
        for token in required_tokens:
            if _normalized_text(token) not in norm:
                errors.append(f"{rel}: critical launcher semantic token missing: {token}")
        if "backend/backend/project" in norm:
            errors.append(f"{rel}: resolves to backend/backend/project")
        if rel.startswith("backend/launchers/") and "../backend/project" in norm:
            errors.append(f"{rel}: prompt trace launcher must target ../project, not ../backend/project")
        if rel.startswith("launchers/") and "../project" in norm and "backend/project" not in norm:
            errors.append(f"{rel}: root workmode launcher must target ../backend/project")
    return errors


def _negative_semantic_self_test() -> list[str]:
    """Ensure this smoke would fail the historical bad path variants."""
    samples = {
        "backend/launchers/run_prompt_trace_smoke_l67214.sh": 'cd "$(dirname "$0")/../backend/project"\nPYTHONPATH=. python3 run_prompt_trace_smoke_l67214.py\n',
        "backend/launchers/run_prompt_trace_smoke_l67214.bat": 'cd /d "%~dp0..\\\\backend\\\\project"\r\npython run_prompt_trace_smoke_l67214.py\r\n',
        "launchers/run_workmode_activation_check_l6718.sh": 'cd "$ROOT/backend/backend/project"\npython -m compileall -q tiangong_agent_runtime\n',
        "launchers/run_workmode_activation_check_l6718.bat": 'cd /d "%~dp0..\\\\backend\\\\backend\\\\project"\r\n"%PYTHON_EXE%" -m compileall -q tiangong_agent_runtime\r\n',
        "frontend/linyuanzhe_frontend/run_desktop_demo.sh": 'python3 run_desktop_demo.py\n',
        "launchers/run_package_builder_preflight_l669.sh": 'python3 scripts/package_builder_preflight_l669.py\n',
        "launchers/run_package_builder_preflight_l669.bat": 'python scripts\\package_builder_preflight_l669.py\r\n',
    }
    missed: list[str] = []
    for rel, text in samples.items():
        norm = _normalized_text(text)
        rel_errors: list[str] = []
        for pattern in BROKEN_PATTERNS:
            if _normalized_text(pattern) in norm:
                rel_errors.append(pattern)
        if "backend/backend/project" in norm:
            rel_errors.append("backend/backend/project")
        if rel.startswith("backend/launchers/") and "../backend/project" in norm:
            rel_errors.append("../backend/project")
        if rel.startswith("launchers/") and "backend/backend/project" in norm:
            rel_errors.append("backend/backend/project")
        if "python" in norm and "PYTHONDONTWRITEBYTECODE" not in text:
            rel_errors.append("wrapper must disable bytecode")
        if re.search(r"(?m)^\s*(?:PYTHONPATH=\S+\s+)?python3?\s+(?!-S\s+-B)", text):
            rel_errors.append("POSIX wrapper must use python -S -B")
        if re.search(r"(?im)^\s*(?:\"%PYTHON_EXE%\"|python)\s+(?!-S\s+-B)", text):
            rel_errors.append("BAT wrapper must use python -S -B")
        if not rel_errors:
            missed.append(rel)
    return [f"negative semantic self-test missed {rel}" for rel in missed]


def _check_script_hygiene(root: Path) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    wrappers = _all_wrappers(root)
    counts = {
        "bat": sum(1 for p in wrappers if p.suffix.lower() == ".bat"),
        "posix": sum(1 for p in wrappers if p.suffix.lower() in {".sh", ".command"}),
        "total": len(wrappers),
    }
    for path in wrappers:
        rel = path.relative_to(root).as_posix()
        data = path.read_bytes()
        bad = [b for b in data if b in BAD_CONTROL and b not in {9, 10, 13}]
        if bad:
            errors.append(f"{rel}: control character 0x{bad[0]:02x}")
        text = data.decode("utf-8", errors="replace")
        norm = _normalized_text(text)
        for pattern in BROKEN_PATTERNS:
            if _normalized_text(pattern) in norm:
                errors.append(f"{rel}: broken launcher path pattern {pattern!r}")
        if re.search(r"(?i)\bpython", text) and "PYTHONDONTWRITEBYTECODE" not in text:
            errors.append(f"{rel}: wrapper executes Python without PYTHONDONTWRITEBYTECODE=1")
        if path.suffix.lower() in {".sh", ".command"}:
            for m in re.finditer(r"(?m)^\s*(?:PYTHONPATH=\S+\s+)?python3?\s+(?!-S\s+-B)", text):
                errors.append(f"{rel}: Python command must use -S -B: {m.group(0).strip()}")
            if re.search(r"(?m)^\s*exec\s+\"\$PYTHON_BIN\"\s+(?!-S\s+-B)", text):
                errors.append(f"{rel}: PYTHON_BIN exec must use -S -B")
        if path.suffix.lower() == ".bat":
            for m in re.finditer(r"(?im)^\s*(?:\"%PYTHON_EXE%\"|python)\s+(?!-S\s+-B)", text):
                errors.append(f"{rel}: Python command must use -S -B: {m.group(0).strip()}")
            if re.search(r"(?i)%PY_CMD%\s+\"%PROBE%\"", text):
                errors.append(f"{rel}: Python probe must use -S -B")
        if re.search(r"reports[\\/]", text):
            errors.append(f"{rel}: wrapper must not write reports into the package tree")
        if path.suffix.lower() == ".bat":
            if b"\r\r\n" in data:
                errors.append(f"{rel}: CRCRLF line ending detected")
            if not _is_crlf_only(data):
                errors.append(f"{rel}: BAT must use CRLF only")
            for m in re.finditer(r"(?im)^\s*cd\s+/d\s+%~dp0[^\r\n]*", text):
                errors.append(f"{rel}: unquoted cd /d %~dp0 path")
        else:
            if not _is_lf_only(data):
                errors.append(f"{rel}: SH/COMMAND must use LF only")
            bash_errors: list[str] = []
            for candidate in _bash_path_candidates(path):
                result = subprocess.run(["bash", "-n", candidate], cwd=str(root), text=True, capture_output=True, timeout=30)
                if result.returncode == 0:
                    break
                bash_errors.append((result.stderr or result.stdout).strip())
            else:
                errors.append(f"{rel}: bash -n failed: {' | '.join(bash_errors[-3:])}")
    return errors, counts


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    cmd = [sys.executable, "-S", str(root / "scripts" / "verify_launchers_l67220.py"), "--root", str(root)]
    result = subprocess.run(cmd, cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(result.stdout, end="")
    errors: list[str] = []
    if result.returncode != 0:
        errors.append(result.stderr.strip() or "manifest launcher verifier failed")
    hygiene_errors, counts = _check_script_hygiene(root)
    errors.extend(hygiene_errors)
    errors.extend(_check_critical_launcher_semantics(root))
    errors.extend(_negative_semantic_self_test())
    if errors:
        for e in errors:
            print("FAIL  " + e, file=sys.stderr)
        return 1
    print(
        "launcher_consistency_smoke PASS: "
        f"manifest entries verified and full wrapper hygiene checked "
        f"({counts['bat']} BAT + {counts['posix']} SH/COMMAND = {counts['total']} wrappers)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
