from __future__ import annotations

"""FE01 STEP31H / L6.70.8 transcript de-duplication aggregate verifier."""

import json
import subprocess
import sys
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


def _run_dedupe_probe() -> dict[str, Any]:
    REPORTS.mkdir(parents=True, exist_ok=True)
    log = REPORTS / "desktop_chat_transcript_dedupe_l6708.log"
    exit_file = REPORTS / "desktop_chat_transcript_dedupe_l6708.exit"
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "desktop_chat_transcript_dedupe_l6708.py")], cwd=str(ROOT), text=True, capture_output=True, timeout=60)
    log.write_text("\n".join(x for x in (proc.stdout, proc.stderr) if x)[-20000:], encoding="utf-8")
    exit_file.write_text(str(proc.returncode), encoding="utf-8")
    return {"name": "desktop_chat_transcript_dedupe_l6708", "ok": proc.returncode == 0, "returncode": proc.returncode, "exit": str(exit_file), "log": str(log)}


def main() -> int:
    dedupe = _run_dedupe_probe()
    desktop = _read_json(REPORTS / "desktop_bundle_preflight_l671.json")
    results = [
        dedupe,
        {"name": "desktop_bundle_preflight_l671", "ok": bool(desktop.get("ok")), "report": str(REPORTS / "desktop_bundle_preflight_l671.json")},
        _exit_ok("l671_desktop_bundle_compileall"),
        _exit_ok("l671_desktop_bundle_scan"),
    ]
    ok = all(item.get("ok") for item in results)
    summary = {
        "contract_version": "tiangong.l6_70_8.desktop_transcript_dedupe_verify.v1",
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
        "note": "L6.70.8 修复桌面端聊天区重复回执与 mock 刷新丢失消息，不替代正式 TiangongWangguan/Runtime 真实联调。",
    }
    out = REPORTS / "validation_summary_l6708.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": ok, "desktop_all_in_one_ready": ok, "ready_for_combine": False, "report": str(out)}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
