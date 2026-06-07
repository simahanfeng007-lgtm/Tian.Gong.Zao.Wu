from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
BACKEND = ROOT / "backend" / "project"
FRONTEND = ROOT / "frontend" / "linyuanzhe_frontend"
FRONTEND_PARENT = ROOT / "frontend"

CONTRACT_VERSION = "tiangong.l6_60.release_verify.v1"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    parts = [str(BACKEND), str(FRONTEND_PARENT)]
    if env.get("PYTHONPATH"):
        parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def _run(name: str, cmd: list[str], *, cwd: Path | None = None, timeout: int = 120, allow_fail: bool = False) -> dict[str, Any]:
    REPORTS.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(cmd, cwd=str(cwd or ROOT), env=_env(), text=True, capture_output=True, timeout=timeout)
    log = REPORTS / f"{name}.log"
    exit_file = REPORTS / f"{name}.exit"
    log.write_text((proc.stdout or "") + ("\n--- STDERR ---\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    exit_file.write_text(str(proc.returncode), encoding="utf-8")
    return {
        "name": name,
        "cmd": [Path(c).name if c.endswith("python") or c.endswith("python3") else c for c in cmd],
        "returncode": proc.returncode,
        "ok": proc.returncode == 0 or allow_fail,
        "allowed_failure": bool(allow_fail and proc.returncode != 0),
        "log": str(log),
        "exit": str(exit_file),
    }


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    steps = []
    steps.append(_run("l660_backend_compileall", [sys.executable, "-m", "compileall", "-q", str(BACKEND)], timeout=180))
    steps.append(_run("l660_frontend_compileall", [sys.executable, "-m", "compileall", "-q", str(FRONTEND), str(ROOT / "launchers"), str(ROOT / "scripts")], timeout=180))
    steps.append(_run("l660_rc_preflight_contract_server", [sys.executable, str(ROOT / "scripts" / "rc_preflight_l659.py"), "--contract-server", "--out", str(REPORTS / "rc_preflight_l660_contract_server.json")], timeout=90))
    steps.append(_run("l660_scan", [sys.executable, str(ROOT / "scripts" / "scan_l659.py")], timeout=90))
    steps.append(_run("l660_real_runtime_gate", [sys.executable, str(ROOT / "scripts" / "real_runtime_gate_l660.py"), "--allow-missing-real", "--out", str(REPORTS / "real_runtime_gate_l660.json")], timeout=90))

    real_gate_payload: dict[str, Any] = {}
    gate_path = REPORTS / "real_runtime_gate_l660.json"
    if gate_path.exists():
        real_gate_payload = json.loads(gate_path.read_text(encoding="utf-8"))

    payload = {
        "contract_version": CONTRACT_VERSION,
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "ok": all(step["ok"] for step in steps),
        "ready_for_combine": bool(real_gate_payload.get("ready_for_combine")),
        "real_runtime_executed": bool(real_gate_payload.get("real_runtime_executed")),
        "merge_blockers": list(real_gate_payload.get("merge_blockers") or []),
        "steps": steps,
        "note": "Contract-server regression may pass while ready_for_combine remains false until the real Runtime gate passes.",
    }
    out = REPORTS / "validation_summary_l660.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": payload["ok"], "ready_for_combine": payload["ready_for_combine"], "real_runtime_executed": payload["real_runtime_executed"], "blockers": payload["merge_blockers"], "report": str(out)}, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
