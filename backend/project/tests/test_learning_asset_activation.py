from __future__ import annotations

import json
from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation


def test_learning_asset_activation_drill_registers_and_calls_learned_assets(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    names = set(runtime.registry.names())
    assert "learning_asset_activation_guide" in names
    assert "learning_asset_activation_apply" in names
    assert "learning_asset_activation_status" in names
    assert "learning_asset_activation_smoke" in names

    result = runtime.run_text("asset-activate drill pytest missing tests", workspace=tmp_path, max_steps=20)
    expected_prefix = [
        "learning_asset_activation_guide",
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
        "learning_asset_activation_apply",
        "learning_asset_activation_smoke",
        "runtime_tool_alignment_check",
        "runtime_llm_operational_drill",
    ]
    assert [step.tool_name for step in result.plan] == expected_prefix
    assert all(item.ok for item in result.results)

    activation = result.results[-4].data
    smoke = result.results[-3].data
    alignment = result.results[-2].data
    assert activation["status"] == "active"
    assert activation["activated_count"] >= 2
    assert smoke["status"] == "pass"
    active_names = [item["tool_name"] for item in activation["activated_assets"]]
    assert any(name.startswith("learned_tool_") for name in active_names)
    assert any(name.startswith("learned_skill_") for name in active_names)
    assert set(active_names).issubset(set(runtime.registry.names()))
    assert alignment["all_tools_have_usage_cards"] is True
    assert alignment["all_registered_tools_classifier_allowed"] is True

    registry_path = Path(activation["registry_path"])
    assert registry_path.exists()
    assert registry_path.is_relative_to(tmp_path)
    persisted = json.loads(registry_path.read_text(encoding="utf-8"))
    assert persisted["status"] == "active"
    assert persisted["active_count"] == activation["active_count"]

    learned_tool = next(name for name in active_names if name.startswith("learned_tool_"))
    direct = runtime.execute_plan(
        [ToolInvocation(learned_tool, {"query": "direct learned tool smoke"})],
        workspace=tmp_path,
        user_message="direct learned tool call",
        max_steps=3,
    )
    assert direct.results[0].ok
    assert direct.results[0].data["status"] == "ok"
    assert direct.results[0].data["data"]["usage_card"]
    assert direct.results[0].data["data"]["call_mode"] == "activated_candidate_adapter"
    assert direct.results[0].data["data"]["candidate_output"]["status"] == "ok"


def test_learning_asset_activation_persists_and_autoloads(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    first = runtime.run_text("asset-activate drill pytest missing tests", workspace=tmp_path, max_steps=20)
    assert all(item.ok for item in first.results)
    active_names = [item["tool_name"] for item in first.results[-4].data["activated_assets"]]
    learned_tool = next(name for name in active_names if name.startswith("learned_tool_"))

    fresh_runtime = RuntimeEntry()
    status = fresh_runtime.run_text("asset-activate status", workspace=tmp_path, max_steps=5)
    assert status.results[0].ok
    assert learned_tool in set(fresh_runtime.registry.names())

    call = fresh_runtime.run_text(f'runtime-tools tool {learned_tool} {{"query":"after reload"}}', workspace=tmp_path, max_steps=5)
    assert call.plan[0].tool_name == learned_tool
    assert call.results[0].ok
    assert call.results[0].data["data"]["arguments"]["query"] == "after reload"
    assert call.results[0].data["data"]["call_mode"] == "activated_candidate_adapter"
    assert call.results[0].data["data"]["candidate_output"]["data"]["arguments"]["query"] == "after reload"
