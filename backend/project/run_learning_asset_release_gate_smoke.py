from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry


def main() -> int:
    workspace = Path(tempfile.mkdtemp(prefix="r19_release_gate_"))
    runtime = RuntimeEntry()
    result = runtime.run_text("asset-release drill pytest missing tests", workspace=workspace, max_steps=16)
    gate = result.results[-1].data if result.results else {}
    report = {
        "ok": all(item.ok for item in result.results) and gate.get("status") == "registration_request_ready",
        "plan": [step.tool_name for step in result.plan],
        "result_statuses": [str(item.status.value) for item in result.results],
        "tool_count": len(runtime.registry.names()),
        "release_gate": gate,
        "workspace": str(workspace),
    }
    out = Path("reports/l6702_r19_release_gate_smoke_report.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
