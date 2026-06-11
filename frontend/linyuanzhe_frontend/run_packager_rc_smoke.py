from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



import json
from pathlib import Path

from linyuanzhe_frontend.clients.mock_runtime_client import MockRuntimeClient
from linyuanzhe_frontend.contracts.installer_rc import installer_rc_policy
from linyuanzhe_frontend.ui.page_specs import PAGE_BY_KEY, FORBIDDEN_HOME_MODULES

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    client = MockRuntimeClient()
    snapshot = client.get_snapshot()
    policy = installer_rc_policy()
    required_files = {
        "installer_manifest_l669": ROOT / "installer" / "installer_manifest_l669.json",
        "build_plan_l669": ROOT / "installer" / "build" / "build_plan_l669.json",
        "package_builder_dry_run_l669": ROOT / "installer" / "build" / "package_builder_dry_run_l669.py",
        "release_manifest_l669": ROOT / "installer" / "release" / "release_manifest_l669.json",
        "signing_policy_l669": ROOT / "installer" / "signing" / "signing_policy_l669.json",
    }
    checks = {
        "installer_page_registered": "installer" in PAGE_BY_KEY,
        "forbidden_auto_update_present": "自动应用更新" in FORBIDDEN_HOME_MODULES,
        "forbidden_frontend_rollback_present": "前端应用回滚" in FORBIDDEN_HOME_MODULES,
        "policy_blocks_frontend_build": policy.get("frontend_may_build_installer") is False,
        "policy_blocks_frontend_update": policy.get("frontend_may_apply_update") is False,
        "policy_blocks_frontend_rollback": policy.get("frontend_may_apply_rollback") is False,
        "identity_preserved": getattr(snapshot.installer_manifest, "unique_developer", "") == "于泳翔" and getattr(snapshot.installer_manifest, "angel_investor", "") == "胖胖龙",
        "required_files_present": all(path.exists() for path in required_files.values()),
    }
    ok = all(checks.values())
    print(json.dumps({"ok": ok, "checks": checks, "required_files": {k: str(v.relative_to(ROOT)) for k, v in required_files.items()}}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
