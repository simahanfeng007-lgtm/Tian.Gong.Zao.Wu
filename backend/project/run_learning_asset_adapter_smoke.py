from __future__ import annotations

import json
from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.learning_asset_adapter import TEMPLATES


def main() -> int:
    workspace = Path(".r21_adapter_smoke_workspace").resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    runtime = RuntimeEntry()
    result = runtime.run_text("asset-adapter drill", workspace=workspace, max_steps=20)
    drill = result.results[3].data if len(result.results) > 3 else {}
    direct_calls = []
    activation = drill.get("activation_report") if isinstance(drill, dict) else {}
    for record in activation.get("activated_assets", []) if isinstance(activation, dict) else []:
        if not isinstance(record, dict):
            continue
        tool_name = str(record.get("tool_name") or "")
        template_id = str(record.get("adapter_template_id") or "")
        if not tool_name.startswith("learned_tool_") or template_id not in TEMPLATES:
            continue
        direct = runtime.execute_plan(
            [ToolInvocation(tool_name, dict(TEMPLATES[template_id].smoke_args))],
            workspace=workspace,
            user_message=f"R21 adapter smoke direct {template_id}",
            max_steps=3,
        )
        item = direct.results[0] if direct.results else None
        direct_calls.append({
            "tool_name": tool_name,
            "adapter_template_id": template_id,
            "ok": bool(item and item.ok),
            "status": item.status.value if item else "missing",
            "output_summary": item.output_summary[:280] if item else "",
            "candidate_status": item.data.get("data", {}).get("candidate_output", {}).get("status") if item and isinstance(item.data, dict) else "",
        })
    report = {
        "schema": "tiangong.l6702.r21.learning_asset_adapter_smoke_report.v1",
        "ok": all(item.ok for item in result.results) and bool(direct_calls) and all(row["ok"] for row in direct_calls),
        "plan": [step.tool_name for step in result.plan],
        "result_statuses": [item.status.value for item in result.results],
        "template_count": 5,
        "runtime_tool_count_after_drill": len(runtime.registry.names()),
        "drill": drill,
        "direct_calls": direct_calls,
    }
    out = Path("reports/l6702_r21_learning_asset_adapter_smoke_report.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "ok": report["ok"],
        "report": str(out),
        "template_count": report["template_count"],
        "runtime_tool_count_after_drill": report["runtime_tool_count_after_drill"],
        "direct_calls": len(direct_calls),
    }, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
