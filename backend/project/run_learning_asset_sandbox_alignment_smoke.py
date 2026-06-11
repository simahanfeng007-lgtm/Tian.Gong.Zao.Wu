from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation


def _compact(label: str, result) -> dict:
    return {
        "label": label,
        "plan_tools": [step.tool_name for step in result.plan],
        "statuses": [item.status.value for item in result.results],
        "ok": all(item.ok for item in result.results),
        "summaries": [item.output_summary[:240] for item in result.results],
        "errors": [item.error_code for item in result.results if item.error_code],
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="learning_asset_sandbox_smoke_") as tmp:
        repo = Path(tmp)
        (repo / "src").mkdir()
        (repo / "src" / "demo.py").write_text("def ok():\n    return True\n", encoding="utf-8")
        runtime = RuntimeEntry()
        direct = runtime.execute_plan(
            [
                ToolInvocation("learning_asset_sandbox_guide", {}),
                ToolInvocation("synthesize_experience_candidates", {"notes": "pytest missing tests，需要最小复测脚手架 Tool 候选", "max_candidates": 8}),
                ToolInvocation("queue_skill_candidates", {"notes": "pytest missing tests", "max_items": 8}),
                ToolInvocation("queue_tool_production_requests", {"notes": "pytest missing tests", "max_items": 8}),
                ToolInvocation("learning_asset_contract_normalize", {"notes": "pytest missing tests", "max_items": 16}),
                ToolInvocation("learning_asset_contract_validate", {}),
                ToolInvocation("learning_asset_sandbox_align", {"notes": "pytest missing tests"}),
                ToolInvocation("learning_asset_sandbox_validate", {"notes": "pytest missing tests"}),
            ],
            workspace=repo,
            user_message="learning asset sandbox alignment direct smoke",
            max_steps=12,
        )
        llm_cases = [
            ("guide", "asset-sandbox guide"),
            ("drill", "asset-sandbox drill pytest missing tests"),
            ("natural", "沙箱对齐 ToolSkill 统一资产"),
        ]
        runs = [_compact(label, runtime.run_text(command, workspace=repo, max_steps=12)) for label, command in llm_cases]
        align = runtime.execute_plan(
            [
                ToolInvocation("runtime_tool_alignment_check", {"include_cards": True}),
                ToolInvocation("runtime_llm_operational_drill", {}),
            ],
            workspace=repo,
            user_message="alignment after R17 sandbox",
            max_steps=5,
        )
        direct_data = direct.results[-1].data if direct.results else {}
        alignment_data = align.results[0].data if align.results else {}
        drill_data = align.results[1].data if len(align.results) > 1 else {}
        payload = {
            "ok": all(item.ok for item in direct.results) and all(row["ok"] for row in runs) and all(item.ok for item in align.results),
            "direct_statuses": [item.status.value for item in direct.results],
            "sandbox_validate_status": direct_data.get("status"),
            "existing_sandbox_found": direct_data.get("existing_sandbox_found"),
            "sandbox_profile": direct_data.get("sandbox_profile"),
            "tool_contract_count": direct_data.get("tool_contract_count"),
            "aligned_tool_contract_count": direct_data.get("aligned_tool_contract_count"),
            "issue_count": direct_data.get("issue_count"),
            "llm_runs": runs,
            "tool_count": alignment_data.get("tool_count"),
            "usage_card_count": alignment_data.get("usage_card_count"),
            "skill_sources": alignment_data.get("skill_sources"),
            "drill_missing_tool_routes": drill_data.get("missing_tool_routes"),
            "drill_empty_routes": drill_data.get("empty_routes"),
        }
        # Q12: keep the report inside the temporary workspace to avoid backend/project/reports pollution.
        out = repo / "l6702_r17_learning_asset_sandbox_alignment_smoke_report.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"ok": payload["ok"], "report": "<tmp>/l6702_r17_learning_asset_sandbox_alignment_smoke_report.json", "tool_count": payload["tool_count"], "sandbox_status": payload["sandbox_validate_status"]}, ensure_ascii=False, indent=2))
        return 0 if payload["ok"] and payload["sandbox_validate_status"] == "pass" and payload["issue_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
