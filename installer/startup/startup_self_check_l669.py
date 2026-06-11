from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPORTS = Path(os.environ.get("LINYUANZHE_REPORT_DIR") or tempfile.mkdtemp(prefix="linyuanzhe_l669_reports_"))


def _check(check_id: str, name: str, ok: bool, message: str, remediation: str = "") -> dict[str, Any]:
    return {
        "check_id": check_id,
        "name": name,
        "status": "pass" if ok else "fail",
        "severity": "info" if ok else "error",
        "message": message,
        "last_run": datetime.now().isoformat(timespec="seconds"),
        "blocks_startup": not ok,
        "remediation_hint": remediation,
    }


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    checks = [
        _check("backend_layout", "后端目录与 run_agent 入口", (ROOT / "backend" / "project" / "run_agent.py").exists(), "后端入口存在" if (ROOT / "backend" / "project" / "run_agent.py").exists() else "后端入口缺失", "确认 backend/project/run_agent.py 随包存在。"),
        _check("frontend_layout", "前端桌面端与 RuntimeClient", (ROOT / "frontend" / "linyuanzhe_frontend" / "app.py").exists(), "前端入口存在" if (ROOT / "frontend" / "linyuanzhe_frontend" / "app.py").exists() else "前端入口缺失", "确认 frontend/linyuanzhe_frontend/app.py 随包存在。"),
        _check("launcher_layout", "统一启动器", (ROOT / "launchers" / "start_linyuanzhe_rc.py").exists(), "统一启动器存在" if (ROOT / "launchers" / "start_linyuanzhe_rc.py").exists() else "统一启动器缺失", "确认 launchers/start_linyuanzhe_rc.py 随包存在。"),
        _check("installer_l668_manifest", "L6.68 安装 manifest", (ROOT / "installer" / "installer_manifest_l668.json").exists(), "L6.68 manifest 存在" if (ROOT / "installer" / "installer_manifest_l668.json").exists() else "L6.68 manifest 缺失", "确认 installer/installer_manifest_l668.json 随包存在。"),
        _check("installer_l669_manifest", "L6.69 打包器 manifest", (ROOT / "installer" / "installer_manifest_l669.json").exists(), "L6.69 manifest 存在" if (ROOT / "installer" / "installer_manifest_l669.json").exists() else "L6.69 manifest 缺失", "确认 installer/installer_manifest_l669.json 随包存在。"),
        _check("build_plan", "Windows 打包计划", (ROOT / "installer" / "build" / "build_plan_l669.json").exists(), "打包计划存在" if (ROOT / "installer" / "build" / "build_plan_l669.json").exists() else "打包计划缺失", "确认 installer/build/build_plan_l669.json 随包存在。"),
        _check("release_manifest", "发布 manifest", (ROOT / "installer" / "release" / "release_manifest_l669.json").exists(), "发布 manifest 存在" if (ROOT / "installer" / "release" / "release_manifest_l669.json").exists() else "发布 manifest 缺失", "确认 installer/release/release_manifest_l669.json 随包存在。"),
        _check("signing_policy", "签名策略占位", (ROOT / "installer" / "signing" / "signing_policy_l669.json").exists(), "签名策略占位存在" if (ROOT / "installer" / "signing" / "signing_policy_l669.json").exists() else "签名策略占位缺失", "确认 installer/signing/signing_policy_l669.json 随包存在。"),
        _check("reports_writable", "报告目录可写", REPORTS.exists() and REPORTS.is_dir(), "报告目录存在", "确认 reports/ 目录可写。"),
    ]
    ok = all(item["status"] == "pass" for item in checks)
    payload = {
        "contract_version": "tiangong.l6_69.startup_self_check.v1",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "ok": ok,
        "checks": checks,
        "final_installer_build_allowed": False,
        "windows_installer_artifact_emitted": False,
        "frontend_applied_update": False,
        "frontend_applied_rollback": False,
        "runtime_core_mutation": False,
    }
    out = REPORTS / "installer_startup_self_check_l669.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": ok, "report": out.name}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
