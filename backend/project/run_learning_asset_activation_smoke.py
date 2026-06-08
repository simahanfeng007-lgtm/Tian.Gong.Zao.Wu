from __future__ import annotations

import json
from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry


def main() -> int:
    workspace = Path(".r20_activation_smoke_workspace").resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    runtime = RuntimeEntry()
    result = runtime.run_text("asset-activate drill pytest missing tests", workspace=workspace, max_steps=20)
    report = {
        "ok": all(item.ok for item in result.results),
        "plan": [step.tool_name for step in result.plan],
        "result_statuses": [item.status.value for item in result.results],
        "activation": result.results[-4].data if len(result.results) >= 4 else {},
        "smoke": result.results[-3].data if len(result.results) >= 3 else {},
    }
    out = Path("reports/l6702_r20_learning_asset_activation_smoke_report.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] and report["activation"].get("status") == "active" and report["smoke"].get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
