from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPORTS = Path(os.environ.get("LINYUANZHE_REPORT_DIR") or tempfile.mkdtemp(prefix="linyuanzhe_startup_l668_"))


def _public_path(path: Path) -> str:
    try:
        tmp = Path(tempfile.gettempdir()).resolve()
        resolved = path.resolve()
        if resolved == tmp or tmp in resolved.parents:
            return f"<tmp>/{resolved.name}"
    except Exception:
        return path.name
    return path.name


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
        _check("installer_manifest", "安装 manifest", (ROOT / "installer" / "installer_manifest_l668.json").exists(), "安装 manifest 存在" if (ROOT / "installer" / "installer_manifest_l668.json").exists() else "安装 manifest 缺失", "确认 installer/installer_manifest_l668.json 随包存在。"),
        _check("reports_writable", "报告目录可写", REPORTS.exists() and REPORTS.is_dir(), "报告目录存在", "确认外部报告目录可写。"),
    ]
    ok = all(item["status"] == "pass" for item in checks)
    payload = {
        "contract_version": "tiangong.l6_68.startup_self_check.v1",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "ok": ok,
        "checks": checks,
        "installer_build_allowed": False,
        "frontend_applied_update": False,
        "frontend_applied_rollback": False,
        "runtime_core_mutation": False,
    }
    out = REPORTS / "installer_startup_self_check_l668.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": ok, "report": _public_path(out)}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
