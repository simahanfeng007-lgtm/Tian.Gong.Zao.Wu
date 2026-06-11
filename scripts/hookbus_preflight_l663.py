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
    from linyuanzhe_frontend.contracts.hook_bus import HOOK_BUS_CONTRACT_VERSION, HookBus, hook_bus_policy
    from linyuanzhe_frontend.contracts.runtime_snapshot import RuntimeSnapshot
    from linyuanzhe_frontend.ui.page_specs import PAGE_BY_KEY

    snapshot = RuntimeSnapshot()
    policy = hook_bus_policy()
    bus = HookBus.default_frontend_bus()
    a5 = bus.evaluate("pre_event_apply", {"event": "quality_gate", "payload": {"risk_level": "A5", "decision": "allowed"}})
    terminal = bus.evaluate("pre_event_apply", {"event": "run_terminal", "payload": {"status": "ok"}, "seen_assistant_final": False})
    chat = bus.evaluate(
        "pre_chat_submit",
        {"payload": {"message": "ok", "no_frontend_tool_execution": True, "no_frontend_memory_write": True, "no_frontend_rollback_apply": True}},
    )
    structure_ok = bool(
        snapshot.hook_bus_contract == HOOK_BUS_CONTRACT_VERSION
        and snapshot.hook_records
        and snapshot.hook_stats
        and "hooks" in PAGE_BY_KEY
        and policy.get("deterministic")
        and policy.get("no_tool_execution")
        and not a5.ok
        and not terminal.ok
        and chat.ok
    )
    smoke = _run("l663_hookbus_smoke", [sys.executable, "-m", "linyuanzhe_frontend.run_hookbus_smoke"], cwd=FRONTEND_PARENT)
    payload = {
        "contract_version": "tiangong.l6_63.hookbus_preflight.v1",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "structure_ok": structure_ok,
        "hook_bus_contract": HOOK_BUS_CONTRACT_VERSION,
        "policy": policy,
        "default_hook_count": len(snapshot.hook_records),
        "default_hook_stats": snapshot.hook_stats,
        "desktop_page_registered": "hooks" in PAGE_BY_KEY,
        "a5_allowed_blocked": not a5.ok,
        "terminal_order_blocked": not terminal.ok,
        "chat_payload_allowed": chat.ok,
        "smoke": smoke,
        "ok": bool(structure_ok and smoke["ok"]),
        "real_runtime_url_present": bool(os.environ.get("LINYUANZHE_RUNTIME_URL", "").strip()),
        "note": "L6.63 只验证 HookBus 确定性规则层；真实 Runtime 解阻仍由 L6.61 脚本负责。",
    }
    out = REPORTS / "hookbus_preflight_l663.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": payload["ok"], "report": str(out)}, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
