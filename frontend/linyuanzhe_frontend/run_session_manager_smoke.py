from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



import json

from linyuanzhe_frontend.clients.mock_runtime_client import MockRuntimeClient
from linyuanzhe_frontend.contracts.runtime_snapshot import safe_text
from linyuanzhe_frontend.ui.page_specs import PAGE_BY_KEY, HOME_ALLOWED_MODULES


def main() -> int:
    client = MockRuntimeClient()
    snapshot = client.get_snapshot()
    sessions = list(getattr(snapshot, "task_sessions", []) or [])
    before_count = len(sessions)
    target = ""
    for item in sessions:
        if getattr(item, "recoverable", False):
            target = safe_text(getattr(item, "session_id_digest", ""), 80)
            break
    target = target or (safe_text(getattr(sessions[0], "session_id_digest", ""), 80) if sessions else "SESS-SMOKE")
    searched = client.request_session_search("恢复")
    resumed = client.request_session_resume(target, "smoke_resume")
    stats = dict(getattr(resumed, "session_stats", {}) or {})
    checks = {
        "sessions_page_registered": "sessions" in PAGE_BY_KEY,
        "home_has_session_entry": "任务 Session 入口" in HOME_ALLOWED_MODULES,
        "session_contract_present": bool(getattr(resumed, "session_manager_contract", "")),
        "session_count_nonzero": before_count > 0 and len(getattr(resumed, "task_sessions", []) or []) > 0,
        "search_recorded": getattr(searched, "session_search_query", "") == "恢复",
        "resume_recorded": safe_text(getattr(resumed, "session_manager_state", ""), 80) in {"frontend_only_recorded", "recoverable", "requested"} or "frontend" in safe_text(getattr(resumed, "session_manager_state", ""), 80),
        "stats_total_present": int(stats.get("total", 0) or 0) >= 1,
        "no_frontend_execution_claim": "前端未直接恢复工具" in safe_text(getattr(resumed, "session_last_message", ""), 240),
    }
    ok = all(checks.values())
    print(json.dumps({"ok": ok, "checks": checks, "session_count": len(getattr(resumed, "task_sessions", []) or []), "target_session": target}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
