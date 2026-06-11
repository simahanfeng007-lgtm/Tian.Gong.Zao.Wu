from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

from tiangong_agent_runtime.runtime_entry import RuntimeEntry


def _report_path() -> Path:
    report_dir = os.environ.get("TIANGONG_REPORT_DIR") or os.environ.get("LINYUANZHE_REPORT_DIR")
    if report_dir:
        return Path(report_dir) / "l6702_r19_learning_asset_release_gate_smoke_report.json"
    return Path(tempfile.mkdtemp(prefix="linyuanzhe_smoke_report_")) / "l6702_r19_learning_asset_release_gate_smoke_report.json"


def _report_label(path: Path) -> str:
    return f"<tmp>/{path.name}" if str(path).startswith(tempfile.gettempdir()) else path.name


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="r19_release_gate_") as tmp:
        workspace = Path(tmp)
        runtime = RuntimeEntry()
        result = runtime.run_text("asset-release drill pytest missing tests", workspace=workspace, max_steps=16)
        gate = result.results[-1].data if result.results else {}
        report = {
        "ok": all(item.ok for item in result.results) and gate.get("status") == "registration_request_ready",
        "plan": [step.tool_name for step in result.plan],
        "result_statuses": [str(item.status.value) for item in result.results],
        "tool_count": len(runtime.registry.names()),
        "release_gate": gate,
        "workspace": "<tmp>/workspace",
    }
        out = _report_path()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"ok": report["ok"], "report": _report_label(out), "workspace": "<tmp>/workspace"}, ensure_ascii=False, indent=2))
        return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
