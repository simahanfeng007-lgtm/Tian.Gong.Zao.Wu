from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WINDOWS_EXT = {".bat", ".cmd", ".ps1"}
SKIP_DIRS = {".git", "__pycache__"}


def _is_under_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def main() -> int:
    bad: list[str] = []
    checked = 0
    for path in ROOT.rglob("*"):
        if not path.is_file() or _is_under_skip(path):
            continue
        if path.suffix.lower() not in WINDOWS_EXT:
            continue
        checked += 1
        data = path.read_bytes()
        lone_lf = data.count(b"\n") - data.count(b"\r\n")
        lone_cr = data.count(b"\r") - data.count(b"\r\n")
        if lone_lf or lone_cr:
            bad.append(f"{path.relative_to(ROOT)} lone_lf={lone_lf} lone_cr={lone_cr}")
    if bad:
        print("[FAIL] Windows launcher line ending audit failed:")
        for item in bad:
            print(" -", item)
        return 1
    print(f"[OK] Windows launcher line ending audit passed. checked={checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
