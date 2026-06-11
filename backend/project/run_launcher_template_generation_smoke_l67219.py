from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

CURRENT_VERSION = "L6.73.8"
CURRENT_MANIFEST = "launcher_manifest_l67220.json"
CURRENT_GENERATOR = "generate_launchers_l67220.py"


def root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def manifest(root: Path) -> dict:
    data = json.loads((root / "scripts" / CURRENT_MANIFEST).read_text(encoding="utf-8"))
    if data.get("version") != CURRENT_VERSION:
        raise AssertionError(f"launcher manifest version drift: {data.get('version')!r}")
    if data.get("generator_id") != f"{CURRENT_VERSION} LauncherTemplateGenerator":
        raise AssertionError(f"launcher generator id drift: {data.get('generator_id')!r}")
    return data


def digest_outputs(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for entry in manifest(root)["entries"]:
        p = root / entry["output_path"]
        out[entry["output_path"]] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def run_generator(root: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    return subprocess.run(
        [sys.executable, "-S", str(root / "scripts" / CURRENT_GENERATOR), "--root", str(root)],
        cwd=str(root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )


def main() -> int:
    root = root_dir()
    before = digest_outputs(root)
    first = run_generator(root)
    if first.returncode != 0:
        print(first.stdout)
        print(first.stderr, file=sys.stderr)
        return first.returncode
    middle = digest_outputs(root)
    second = run_generator(root)
    if second.returncode != 0:
        print(second.stdout)
        print(second.stderr, file=sys.stderr)
        return second.returncode
    after = digest_outputs(root)
    if before != middle or middle != after:
        print("launcher_template_generation_smoke FAIL: current generator is not idempotent", file=sys.stderr)
        return 1
    print(f"launcher_template_generation_smoke PASS: {len(after)} current launchers unchanged across two runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
