from __future__ import annotations

"""FE01 STEP31F / L6.70.6 desktop visual-click aggregate verifier."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"read_error": str(exc)[:200]}


def _exit_ok(name: str) -> dict[str, Any]:
    p = REPORTS / f"{name}.exit"
    if not p.exists():
        return {"name": name, "ok": False, "returncode": 1, "reason": "missing exit evidence"}
    try:
        rc = int((p.read_text(encoding="utf-8").strip() or "1"))
    except ValueError:
        rc = 1
    return {"name": name, "ok": rc == 0, "returncode": rc, "exit": str(p), "log": str(REPORTS / f"{name}.log")}


def main() -> int:
    desktop = _read_json(REPORTS / "desktop_bundle_preflight_l671.json")
    results = [
        {"name": "desktop_bundle_preflight_l671", "ok": bool(desktop.get("ok")), "report": str(REPORTS / "desktop_bundle_preflight_l671.json")},
        _exit_ok("l671_desktop_bundle_compileall"),
        _exit_ok("l671_desktop_bundle_scan"),
    ]
    ok = all(item.get("ok") for item in results)
    summary = {
        "contract_version": "tiangong.l6_70_6.desktop_visual_click_verify.v1",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "ok": ok,
        "desktop_all_in_one_ready": ok,
        "frontend_backend_bundled": True,
        "local_desktop_bridge_ready": bool(desktop.get("local_desktop_bridge_ready")),
        "real_runtime_smoke_passed": False,
        "ready_for_combine": False,
        "final_installer_allowed": False,
        "windows_installer_artifact_emitted": False,
        "runtime_core_mutation": False,
        "results": results,
        "merge_blockers": ["official real Runtime RC unlock not executed; desktop local bridge is not final RC evidence"],
        "note": "L6.70.6 是桌面端全量视觉点击体感修复包，不是正式 exe/msi 安装器，也不把本地桥接冒充真实 Runtime。",
    }
    out = REPORTS / "validation_summary_l671.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": ok, "desktop_all_in_one_ready": ok, "ready_for_combine": False, "report": str(out)}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
