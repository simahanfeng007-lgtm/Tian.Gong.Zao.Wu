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


def _env() -> dict[str, str]:
    env = os.environ.copy()
    parts = [str(BACKEND), str(FRONTEND_PARENT)]
    if env.get("PYTHONPATH"):
        parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def _run(name: str, cmd: list[str], *, cwd: Path = ROOT, timeout: int = 90) -> dict[str, Any]:
    REPORTS.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(cmd, cwd=str(cwd), env=_env(), text=True, capture_output=True, timeout=timeout)
    (REPORTS / f"{name}.log").write_text((proc.stdout or "") + ("\n--- STDERR ---\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    (REPORTS / f"{name}.exit").write_text(str(proc.returncode), encoding="utf-8")
    return {"name": name, "returncode": proc.returncode, "ok": proc.returncode == 0, "log": str(REPORTS / f"{name}.log")}


def main(argv: list[str] | None = None) -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(FRONTEND_PARENT))
    from linyuanzhe_frontend.contracts.observability import OBSERVABILITY_CONTRACT_VERSION, observability_policy
    from linyuanzhe_frontend.contracts.runtime_snapshot import RuntimeSnapshot
    from linyuanzhe_frontend.ui.page_specs import PAGE_BY_KEY

    snapshot = RuntimeSnapshot()
    structure_ok = bool(
        snapshot.observability_contract == OBSERVABILITY_CONTRACT_VERSION
        and snapshot.trace_records
        and snapshot.trace_stats
        and "observability" in PAGE_BY_KEY
    )
    smoke = _run("l662_observability_smoke", [sys.executable, "-m", "linyuanzhe_frontend.run_observability_smoke"], cwd=FRONTEND_PARENT)
    payload = {
        "contract_version": "tiangong.l6_62.observability_preflight.v1",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "structure_ok": structure_ok,
        "observability_contract": OBSERVABILITY_CONTRACT_VERSION,
        "policy": observability_policy(),
        "default_trace_count": len(snapshot.trace_records),
        "default_trace_stats": snapshot.trace_stats,
        "desktop_page_registered": "observability" in PAGE_BY_KEY,
        "smoke": smoke,
        "ok": bool(structure_ok and smoke["ok"]),
        "real_runtime_url_present": bool(os.environ.get("LINYUANZHE_RUNTIME_URL", "").strip()),
        "note": "L6.62 只验证观测台只读投影；真实 Runtime 解阻仍由 L6.61 脚本负责。",
    }
    out = REPORTS / "observability_preflight_l662.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": payload["ok"], "report": str(out)}, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
