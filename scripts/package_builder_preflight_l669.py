from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "project"
FRONTEND_PARENT = ROOT / "frontend"


def _default_report_dir() -> Path:
    env_dir = os.environ.get("LINYUANZHE_REPORT_DIR", "").strip()
    if env_dir:
        return Path(env_dir)
    return Path(tempfile.mkdtemp(prefix="linyuanzhe_l669_reports_"))


def _public_path(path: Path, report_dir: Path) -> str:
    try:
        return path.resolve().relative_to(report_dir.resolve()).as_posix()
    except ValueError:
        return f"<tmp>/{path.name}" if str(report_dir).startswith(tempfile.gettempdir()) else path.name


def _env(report_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    parts = [str(BACKEND), str(FRONTEND_PARENT)]
    if env.get("PYTHONPATH"):
        parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(parts)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["LINYUANZHE_REPORT_DIR"] = str(report_dir)
    return env


def _run(name: str, cmd: list[str], cwd: Path, report_dir: Path) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=str(cwd), env=_env(report_dir), text=True, capture_output=True, timeout=180)
    log = report_dir / f"l669_{name}.log"
    log.write_text((proc.stdout or "") + ("\n--- STDERR ---\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    payload: dict[str, Any] = {}
    if proc.stdout.strip():
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload = {"parse_error": "stdout was not json"}
    return {"name": name, "returncode": proc.returncode, "ok": proc.returncode == 0 and bool(payload.get("ok", True)), "log": _public_path(log, report_dir), "payload": payload}


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="L6.69 package-builder preflight")
    parser.add_argument("--report-dir", default=str(_default_report_dir()), help="报告目录；默认写入临时目录，不污染交付树。")
    args = parser.parse_args(argv)
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    runs = [
        _run("packager_rc_smoke", [sys.executable, "-S", "-B", "-m", "linyuanzhe_frontend.run_packager_rc_smoke"], FRONTEND_PARENT, report_dir),
        _run("startup_self_check_l669", [sys.executable, "-S", "-B", str(ROOT / "installer" / "startup" / "startup_self_check_l669.py")], ROOT, report_dir),
        _run("version_slot_validation_l669", [sys.executable, "-S", "-B", str(ROOT / "installer" / "build" / "version_slot_validate_l669.py")], ROOT, report_dir),
        _run("windows_packager_dry_run_l669", [sys.executable, "-S", "-B", str(ROOT / "installer" / "build" / "package_builder_dry_run_l669.py"), "--out", str(report_dir / "windows_packager_dry_run_l669.json")], ROOT, report_dir),
        _run("release_pipeline_preflight_l669", [sys.executable, "-S", "-B", str(ROOT / "installer" / "release" / "release_pipeline_preflight_l669.py")], ROOT, report_dir),
    ]
    summary = {
        "contract_version": "tiangong.l6_69.package_builder_preflight.v1",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "ok": all(item["ok"] for item in runs),
        "runs": runs,
        "dry_run_only": True,
        "final_installer_allowed": False,
        "windows_installer_artifact_emitted": False,
        "frontend_built_installer": False,
        "runtime_core_mutation": False,
        "ready_for_combine": False,
        "merge_blockers": ["real Runtime instance smoke not executed"],
    }
    out = report_dir / "package_builder_preflight_l669.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": summary["ok"], "ready_for_combine": False, "report": _public_path(out, report_dir)}, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
