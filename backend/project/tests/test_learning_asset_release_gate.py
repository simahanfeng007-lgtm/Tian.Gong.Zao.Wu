from __future__ import annotations

import json
from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation


def test_learning_asset_release_gate_drill_is_execution_first(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    names = set(runtime.registry.names())
    assert "learning_asset_release_gate_guide" in names
    assert "learning_asset_release_gate_check" in names

    result = runtime.run_text("asset-release drill pytest missing tests", workspace=tmp_path, max_steps=16)
    assert [step.tool_name for step in result.plan] == [
        "learning_asset_release_gate_guide",
        "synthesize_experience_candidates",
        "queue_skill_candidates",
        "queue_tool_production_requests",
        "learning_asset_contract_normalize",
        "learning_asset_contract_validate",
        "learning_asset_sandbox_align",
        "learning_asset_sandbox_validate",
        "learning_asset_candidate_sandbox_build",
        "learning_asset_candidate_sandbox_validate",
        "learning_asset_candidate_sandbox_review",
        "learning_asset_release_gate_check",
    ]
    assert all(item.ok for item in result.results)
    gate = result.results[-1].data
    assert gate["status"] == "registration_request_ready"
    assert gate["quality_gate"]["decision"] == "pass"
    assert gate["release_gate"]["decision"] == "pass"
    assert gate["registration_request"]["ready"] is True
    assert gate["registration_request"]["runtime_registration_allowed_now"] is False
    assert gate["registration_request"]["skill_registry_write_allowed_now"] is False
    assert gate["release_gate"]["allow_activation_now"] is False
    assert gate["package_count"] >= 2
    report_path = Path(gate["report_path"])
    assert report_path.exists()
    assert report_path.is_relative_to(tmp_path)
    persisted = json.loads(report_path.read_text(encoding="utf-8"))
    assert persisted["status"] == "registration_request_ready"


def test_learning_asset_release_gate_registry_alignment(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    result = runtime.execute_plan(
        [
            ToolInvocation("runtime_tool_alignment_check", {"include_cards": True}),
            ToolInvocation("runtime_llm_operational_drill", {}),
        ],
        workspace=tmp_path,
        user_message="r19 asset release gate alignment",
        max_steps=5,
    )
    assert all(item.ok for item in result.results)
    report = result.results[0].data
    assert report["tool_count"] == len(runtime.registry.names())
    assert report["usage_card_count"] == report["tool_count"]
    assert report["all_tools_have_usage_cards"] is True
    assert report["all_registered_tools_classifier_allowed"] is True
    assert "skill.learning_asset_release_gate_workflow" in report["skill_sources"]
    cards = {card["tool"]: card for card in report["tool_usage_cards"]}
    assert cards["learning_asset_release_gate_check"]["family"] == "learning_asset_release_gate"
    drill = result.results[1].data
    assert drill["missing_tool_routes"] == []
    assert drill["empty_routes"] == []
