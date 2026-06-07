from __future__ import annotations

import json

from linyuanzhe_frontend.clients.mock_runtime_client import MockRuntimeClient
from linyuanzhe_frontend.contracts.installer_rc import installer_rc_policy, summarize_checks
from linyuanzhe_frontend.ui.page_specs import PAGE_BY_KEY, HOME_ALLOWED_MODULES, FORBIDDEN_HOME_MODULES


def main() -> int:
    client = MockRuntimeClient()
    snapshot = client.get_snapshot()
    checks = list(getattr(snapshot, "startup_self_checks", []) or [])
    summary = summarize_checks(checks)
    policy = installer_rc_policy()
    snap_dict = snapshot.to_dict()
    checks_map = {
        "installer_page_registered": "installer" in PAGE_BY_KEY,
        "home_has_installer_entry": "安装器 RC 状态入口" in HOME_ALLOWED_MODULES,
        "forbidden_auto_update_present": "自动应用更新" in FORBIDDEN_HOME_MODULES,
        "installer_contract_present": getattr(snapshot, "installer_rc_contract", "") == "tiangong.l6_68.installer_rc.v1",
        "identity_preserved": getattr(snapshot.installer_manifest, "unique_developer", "") == "于泳翔" and getattr(snapshot.installer_manifest, "angel_investor", "") == "胖胖龙",
        "version_slots_present": len(getattr(snapshot, "version_slots", []) or []) >= 3,
        "startup_checks_present": summary.get("total", 0) >= 4,
        "crash_report_local_only": all(getattr(item, "local_only", True) and not getattr(item, "upload_allowed", False) for item in getattr(snapshot, "crash_report_records", []) or []),
        "repair_actions_no_frontend_apply": all(getattr(item, "no_frontend_apply", True) for item in getattr(snapshot, "repair_action_records", []) or []),
        "policy_blocks_frontend_apply": not policy["frontend_may_apply_update"] and not policy["frontend_may_apply_rollback"] and not policy["frontend_may_build_installer"],
        "snapshot_serializes": "installer_manifest" in snap_dict and "version_slots" in snap_dict,
    }
    ok = all(checks_map.values())
    print(json.dumps({"ok": ok, "checks": checks_map, "startup_summary": summary, "slot_count": len(getattr(snapshot, "version_slots", []) or [])}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
