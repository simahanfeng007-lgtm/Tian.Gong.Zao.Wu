from __future__ import annotations

from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation


def test_learning_asset_contract_registered_and_validate_pass(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    names = set(runtime.registry.names())
    assert "learning_asset_contract_guide" in names
    assert "learning_asset_contract_normalize" in names
    assert "learning_asset_contract_validate" in names

    result = runtime.execute_plan(
        [
            ToolInvocation("learning_asset_contract_guide", {}),
            ToolInvocation("synthesize_experience_candidates", {"notes": "未来所有自主学习和总结经验生产的 tool 和 skill 格式统一", "max_candidates": 8}),
            ToolInvocation("queue_skill_candidates", {"notes": "未来统一格式", "max_items": 8}),
            ToolInvocation("queue_tool_production_requests", {"notes": "未来统一格式", "max_items": 8}),
            ToolInvocation("learning_asset_contract_normalize", {"notes": "未来统一格式", "max_items": 16}),
            ToolInvocation("learning_asset_contract_validate", {}),
        ],
        workspace=tmp_path,
        user_message="learning asset contract test",
        max_steps=10,
    )
    assert [item.status.value for item in result.results] == ["ok", "ok", "ok", "ok", "ok", "ok"]
    normalize = result.results[-2].data
    validate = result.results[-1].data
    assert normalize["schema"] == "tiangong.l6702.r16.learning_asset_contract.v1"
    assert normalize["contract_count"] >= 1
    assert normalize["issue_count"] == 0
    assert validate["status"] == "pass"
    assert validate["issue_count"] == 0
    first = validate["contracts"][0]
    assert first["usage_card"]["when_to_use"]
    assert first["chain_recipe"]
    assert first["llm_policy"]["llm_is_final_decider"] is True
    assert first["candidate_only"] is True
    assert first["no_tool_registration"] is True


def test_learning_asset_contract_planbridge_and_alignment(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    drill = runtime.run_text("asset-contract drill 未来所有自主学习总结经验生产 tool skill 格式统一", workspace=tmp_path, max_steps=20)
    assert [step.tool_name for step in drill.plan] == [
        "synthesize_experience_candidates",
        "queue_skill_candidates",
        "queue_tool_production_requests",
        "learning_asset_contract_normalize",
        "learning_asset_contract_validate",
    ]
    assert all(item.ok for item in drill.results)
    natural = runtime.run_text("自主学习总结经验生产tool和skill格式统一", workspace=tmp_path, max_steps=10)
    assert natural.plan[0].tool_name == "learning_asset_contract_guide"
    assert all(item.ok for item in natural.results)

    alignment = runtime.execute_plan(
        [
            ToolInvocation("runtime_tool_alignment_check", {"include_cards": True}),
            ToolInvocation("runtime_llm_operational_drill", {}),
        ],
        workspace=tmp_path,
        user_message="r16 alignment",
        max_steps=5,
    )
    assert all(item.ok for item in alignment.results)
    report = alignment.results[0].data
    assert report["tool_count"] == len(runtime.registry.names())
    assert report["usage_card_count"] == report["tool_count"]
    assert "skill.learning_asset_contract_workflow" in report["skill_sources"]
    cards = {card["tool"]: card for card in report["tool_usage_cards"]}
    assert cards["learning_asset_contract_normalize"]["family"] == "learning_asset_contract"
    assert alignment.results[1].data["missing_tool_routes"] == []
    assert alignment.results[1].data["empty_routes"] == []
