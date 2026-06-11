from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from time import time

from tiangong_agent_runtime.runtime_entry import RuntimeEntry

SCHEMA = "tiangong.l6721_1.active_assets_relocation_smoke.v3"


def _report_path() -> Path:
    report_dir = os.environ.get("TIANGONG_REPORT_DIR") or os.environ.get("LINYUANZHE_REPORT_DIR")
    if report_dir:
        return Path(report_dir) / "L6721_1_ACTIVE_ASSETS_RELOCATION_SMOKE.json"
    return Path(tempfile.mkdtemp(prefix="l67211_active_assets_report_")) / "L6721_1_ACTIVE_ASSETS_RELOCATION_SMOKE.json"


def _stale_registry_paths(registry_path: Path) -> int:
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    count = 0
    for record in payload.get("records", []):
        if not isinstance(record, dict):
            continue
        current_name = Path(str(record.get("active_dir") or record.get("active_dir_relative") or "asset")).name
        record.pop("active_dir_relative", None)
        record.pop("active_manifest_relative", None)
        record["active_dir"] = f"/stale/build/root/{current_name}"
        record["active_manifest_path"] = f"/stale/build/root/{current_name}/activation_manifest.json"
        count += 1
    registry_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return count


def _seed_active_assets(workspace: Path) -> dict:
    """Build a temporary active asset fixture instead of relying on delivery-time .linyuanzhe."""
    workspace.mkdir(parents=True, exist_ok=True)
    runtime = RuntimeEntry()
    drill = runtime.run_text("asset-activate drill pytest missing tests", workspace=workspace, max_steps=20)
    ok = bool(drill.results) and all(item.ok for item in drill.results)
    active_root = workspace / ".linyuanzhe" / "active_assets"
    registry_path = active_root / "r20" / "active_assets_registry.json"
    if not ok or not registry_path.exists():
        raise RuntimeError("failed to create temporary active asset fixture")
    return {"runtime": runtime, "drill_ok": ok, "active_root": active_root, "registry_path": registry_path}


def main() -> int:
    report_path = _report_path()
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="l6721_1_current_") as current_tmp, tempfile.TemporaryDirectory(prefix="l6721_1_relocate_") as relocate_tmp:
        current_workspace = Path(current_tmp) / "current_workspace"
        seeded = _seed_active_assets(current_workspace)
        current_runtime = RuntimeEntry()
        current_smoke = current_runtime.run_text("asset-activate smoke current workspace", workspace=current_workspace, max_steps=8)
        current_ok = bool(current_smoke.results and current_smoke.results[0].ok)

        relocated_workspace = Path(relocate_tmp) / "relocated_workspace"
        relocated_active = relocated_workspace / ".linyuanzhe" / "active_assets"
        relocated_active.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(seeded["active_root"], relocated_active)
        registry_path = relocated_active / "r20" / "active_assets_registry.json"
        stale_count = _stale_registry_paths(registry_path)

        fresh_runtime = RuntimeEntry()
        status = fresh_runtime.run_text("asset-activate status relocated package", workspace=relocated_workspace, max_steps=8)
        smoke = fresh_runtime.run_text("asset-activate smoke relocated package", workspace=relocated_workspace, max_steps=8)
        status_data = status.results[0].data if status.results else {}
        smoke_data = smoke.results[0].data if smoke.results else {}
        relocated_ok = bool(status.results and status.results[0].ok and smoke.results and smoke.results[0].ok)

    report = {
        "schema": SCHEMA,
        "generated_at": time(),
        "status": "pass" if current_ok and relocated_ok else "failed",
        "current_workspace_smoke_ok": current_ok,
        "relocated_workspace_ok": relocated_ok,
        "stale_record_count": stale_count,
        "status_active_count": status_data.get("active_count"),
        "status_issue_count": status_data.get("issue_count"),
        "status_relocated_count": status_data.get("relocated_count"),
        "smoke_status": smoke_data.get("status"),
        "smoke_count": smoke_data.get("smoke_count"),
        "smoke_issue_count": smoke_data.get("issue_count"),
        "path_mode": status_data.get("path_mode"),
        "relocation_supported": status_data.get("relocation_supported"),
        "llm_final_decision_required": True,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": "<tmp>/L6721_1_ACTIVE_ASSETS_RELOCATION_SMOKE.json", "workspace_mode": "temporary_cleaned"}, ensure_ascii=False))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
