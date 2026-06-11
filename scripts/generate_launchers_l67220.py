from __future__ import annotations

"""L6.73.8 launcher template generator.

This generator is deliberately small and standard-library only. It turns the
single manifest + templates into all user-facing BAT/SH/COMMAND launchers so
entry scripts do not drift by copy/paste.
"""

import argparse
import json
import os
import stat
from pathlib import Path
from typing import Any

DEFAULT_VERSION = "L6.73.8"
MANIFEST_REL = Path("scripts/launcher_manifest_l67220.json")
GENERATOR_ID = "L6.73.8 LauncherTemplateGenerator"


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_manifest(root: Path) -> dict[str, Any]:
    path = root / MANIFEST_REL
    with path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)
    if manifest.get("schema") != "launcher_manifest_l67220.v1":
        raise SystemExit(f"Unsupported launcher manifest schema: {manifest.get('schema')!r}")
    return manifest


def render(template: str, variables: dict[str, str]) -> str:
    out = template
    for key, value in variables.items():
        out = out.replace("{{" + key + "}}", value)
    leftovers = sorted({part.split("}}", 1)[0] for part in out.split("{{")[1:] if "}}" in part})
    if leftovers:
        raise ValueError(f"Unresolved template variables: {leftovers}")
    return out


def normalize_windows_rel(path: str) -> str:
    return path.replace("/", "\\")


def read_template(root: Path, manifest: dict[str, Any], platform: str) -> tuple[str, str]:
    templates = manifest.get("templates", {})
    rel = templates.get(platform)
    if not rel:
        raise ValueError(f"No template for platform {platform}")
    path = root / rel
    return rel, path.read_text(encoding="utf-8")


def desired_content(root: Path, manifest: dict[str, Any], entry: dict[str, Any]) -> tuple[bytes, str]:
    platform = entry["platform"]
    template_rel, template = read_template(root, manifest, platform)
    title = entry.get("title") or f"FE01 STEP68 / {manifest['version']} - {entry['entry_kind']}"
    variables = {
        "GENERATOR_ID": manifest.get("generator_id", GENERATOR_ID),
        "VERSION": manifest.get("version", DEFAULT_VERSION),
        "TITLE": title,
        "PY_ENTRY_POSIX": entry["python_entry"].replace("\\", "/"),
        "PY_ENTRY_WIN": normalize_windows_rel(entry["python_entry"]),
        "ENTRY_KIND": entry["entry_kind"],
        "PYTHON_PROBE_POSIX": entry.get("python_probe", manifest.get("python_probe", "")).replace("\\", "/"),
        "PYTHON_PROBE_WIN": normalize_windows_rel(entry.get("python_probe", manifest.get("python_probe", ""))),
        "ROOT_HINT_KEY": manifest.get("root_hint_key", "LINYUANZHE_ROOT_HINT"),
        "EXTRA_ARGS": entry.get("extra_args", "").strip(),
        "PYTHON_MODE": entry.get("python_mode", "plain"),
        "TEMPLATE_NAME": Path(template_rel).name,
    }
    text = render(template, variables)
    if platform == "windows":
        # BAT must be ASCII and CRLF. Keep messages in ASCII to avoid codepage drift.
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        data = text.replace("\n", "\r\n").encode("ascii")
    else:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        data = text.encode("utf-8")
    return data, template_rel


def write_if_changed(path: Path, data: bytes, *, executable: bool) -> str:
    old = path.read_bytes() if path.exists() else None
    if old == data:
        action = "unchanged"
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        action = "written" if old is None else "updated"
    if executable:
        current = path.stat().st_mode
        path.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return action


def generate(root: Path, *, check: bool = False) -> list[dict[str, str]]:
    manifest = load_manifest(root)
    rows: list[dict[str, str]] = []
    for entry in manifest["entries"]:
        data, template_rel = desired_content(root, manifest, entry)
        output = root / entry["output_path"]
        action = "would_write"
        if check:
            if output.exists() and output.read_bytes() == data:
                action = "unchanged"
            elif output.exists():
                action = "would_update"
            else:
                action = "would_create"
        else:
            action = write_if_changed(output, data, executable=entry["platform"] in {"linux", "macos"})
        rows.append({
            "name": entry["name"],
            "platform": entry["platform"],
            "entry_kind": entry["entry_kind"],
            "output_path": entry["output_path"],
            "template": template_rel,
            "action": action,
        })
    return rows


def main() -> int:
    p = argparse.ArgumentParser(description="Generate L6.73.8 launchers from templates.")
    p.add_argument("--root", default=str(project_root()), help="Project root. Defaults to this script's parent project root.")
    p.add_argument("--check", action="store_true", help="Do not write; report whether files would change.")
    args = p.parse_args()
    root = Path(args.root).resolve()
    rows = generate(root, check=args.check)
    for row in rows:
        print(f"{row['action']:>12}  {row['platform']:<7}  {row['entry_kind']:<22}  {row['output_path']}")
    print(f"[L6.73.8] launcher generation complete: {len(rows)} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
