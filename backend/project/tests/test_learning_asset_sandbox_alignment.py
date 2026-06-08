from __future__ import annotations

from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation


def test_learning_asset_sandbox_alignment_registered_and_pass(tmp_path) -> None:
    runtime = RuntimeEntry()
    names = set(runtime.registry.names())
    assert "learning_asset_sandbox_guide" in names
    assert "learning_asset_sandbox_align" in names
    assert "learning_asset_sandbox_validate" in names

    result = runtime.execute_plan(
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
        workspace=tmp_path,
        user_message="asset sandbox alignment test",
        max_steps=12,
    )
    assert [item.status.value for item in result.results] == ["ok"] * len(result.results)
    align = result.results[-2].data
    validate = result.results[-1].data
    assert align["existing_sandbox_found"] is True
    assert align["sandbox_profile"] == "isolated_workspace_candidate_only"
    assert align["tool_contract_count"] >= 1
    assert align["production_request_count"] >= 1
    assert align["sandbox_plan_count"] >= 1
    assert align["aligned_tool_contract_count"] == align["tool_contract_count"]
    assert validate["status"] == "pass"
    assert validate["issue_count"] == 0


def test_learning_asset_sandbox_planbridge_and_global_alignment(tmp_path) -> None:
    runtime = RuntimeEntry()
    drill = runtime.run_text("asset-sandbox drill pytest missing tests", workspace=tmp_path, max_steps=12)
    assert [step.tool_name for step in drill.plan] == [
        "learning_asset_sandbox_guide",
        "synthesize_experience_candidates",
        "queue_skill_candidates",
        "queue_tool_production_requests",
        "learning_asset_contract_normalize",
        "learning_asset_contract_validate",
        "learning_asset_sandbox_align",
        "learning_asset_sandbox_validate",
    ]
    assert all(item.ok for item in drill.results)

    natural = runtime.run_text("沙箱对齐 ToolSkill 统一资产", workspace=tmp_path, max_steps=12)
    assert natural.plan[0].tool_name == "learning_asset_sandbox_guide"
    assert all(item.ok for item in natural.results)

    alignment = runtime.execute_plan(
        [
            ToolInvocation("runtime_tool_alignment_check", {"include_cards": True}),
            ToolInvocation("runtime_llm_operational_drill", {}),
        ],
        workspace=tmp_path,
        user_message="r17 sandbox alignment",
        max_steps=5,
    )
    assert all(item.ok for item in alignment.results)
    report = alignment.results[0].data
    assert report["tool_count"] == len(runtime.registry.names())
    assert report["usage_card_count"] == report["tool_count"]
    assert "skill.learning_asset_sandbox_alignment_workflow" in report["skill_sources"]
    cards = {card["tool"]: card for card in report["tool_usage_cards"]}
    assert cards["learning_asset_sandbox_align"]["family"] == "learning_asset_sandbox_alignment"
    drill_report = alignment.results[1].data
    assert drill_report["missing_tool_routes"] == []
    assert drill_report["empty_routes"] == []
