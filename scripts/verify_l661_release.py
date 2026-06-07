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
FRONTEND_PARENT = ROOT / "frontend"


def _run(name: str, cmd: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None, allow: set[int] | None = None, timeout: int = 120) -> dict[str, Any]:
    allow = allow or {0}
    REPORTS.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(cmd, cwd=str(cwd), env=env, text=True, capture_output=True, timeout=timeout)
    (REPORTS / f"{name}.log").write_text((proc.stdout or "") + ("\n--- STDERR ---\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    (REPORTS / f"{name}.exit").write_text(str(proc.returncode), encoding="utf-8")
    return {"name": name, "cmd": [Path(x).name if x == sys.executable else x for x in cmd], "returncode": proc.returncode, "ok": proc.returncode in allow, "log": str(REPORTS / f"{name}.log")}


def _env() -> dict[str, str]:
    env = os.environ.copy()
    parts = [str(BACKEND), str(FRONTEND_PARENT)]
    if env.get("PYTHONPATH"):
        parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def main() -> int:
    env = _env()
    results = []
    results.append(_run("l661_backend_compileall", [sys.executable, "-m", "compileall", "-q", str(BACKEND)], env=env, timeout=180))
    results.append(_run("l661_frontend_scripts_compileall", [sys.executable, "-m", "compileall", "-q", str(FRONTEND_PARENT), str(ROOT / "scripts"), str(ROOT / "launchers")], env=env, timeout=180))
    results.append(_run("l661_rc_preflight_contract_server", [sys.executable, str(ROOT / "scripts" / "rc_preflight_l659.py"), "--contract-server", "--out", str(REPORTS / "rc_preflight_l661_contract_server.json")], env=env, timeout=120))
    runtime_present = bool(env.get("LINYUANZHE_RUNTIME_URL", "").strip())
    if runtime_present:
        results.append(_run("l661_real_runtime_unlock", [sys.executable, str(ROOT / "scripts" / "real_runtime_unlock_l661.py"), "--require-real", "--out", str(REPORTS / "real_runtime_unlock_l661_verify.json")], env=env, allow={0, 2}, timeout=180))
    else:
        clean_env = dict(env)
        clean_env.pop("LINYUANZHE_RUNTIME_URL", None)
        results.append(_run("l661_real_runtime_unlock_absent_expected", [sys.executable, str(ROOT / "scripts" / "real_runtime_unlock_l661.py"), "--require-real", "--out", str(REPORTS / "real_runtime_unlock_l661_absent_expected.json")], env=clean_env, allow={2}, timeout=60))
    results.append(_run("l661_scan", [sys.executable, str(ROOT / "scripts" / "scan_l659.py")], env=env, timeout=120))
    summary = {
        "contract_version": "tiangong.l6_61.release_verify.v1",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "runtime_url_present": runtime_present,
        "results": results,
        "ok": all(item["ok"] for item in results),
        "ready_for_combine": False,
        "note": "runtime_url_present=false 时，真实联调缺席返回 2 被视为正确阻断，不代表 RC 已解阻。",
    }
    # If real unlock report says ready, surface it.
    real_report = REPORTS / "real_runtime_unlock_l661_verify.json"
    if real_report.exists():
        try:
            real_payload = json.loads(real_report.read_text(encoding="utf-8"))
            summary["ready_for_combine"] = bool(real_payload.get("ready_for_combine"))
        except Exception as exc:
            summary["real_unlock_report_read_error"] = str(exc)[:160]
    out = REPORTS / "validation_summary_l661.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": summary["ok"], "ready_for_combine": summary["ready_for_combine"], "report": str(out)}, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
