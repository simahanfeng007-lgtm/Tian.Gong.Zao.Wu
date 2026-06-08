from __future__ import annotations

from pathlib import Path

from tiangong_agent_runtime.learning_asset_adapter import TEMPLATES
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation


EXPECTED_TEMPLATE_IDS = {
    "pure_transform",
    "schema_contract_check",
    "project_diagnostic",
    "doc_skill_production",
    "experience_reuse",
}


def test_learning_asset_adapter_template_tools_are_registered_and_smoke(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    names = set(runtime.registry.names())
    for tool_name in (
        "learning_asset_adapter_guide",
        "learning_asset_adapter_template_list",
        "learning_asset_adapter_template_normalize",
        "learning_asset_adapter_template_validate",
        "learning_asset_adapter_template_smoke",
        "learning_asset_adapter_drill",
    ):
        assert tool_name in names

    templates = runtime.run_text("asset-adapter templates", workspace=tmp_path, max_steps=3)
    assert templates.plan[0].tool_name == "learning_asset_adapter_template_list"
    assert templates.results[0].ok
    assert {item["template_id"] for item in templates.results[0].data["templates"]} == EXPECTED_TEMPLATE_IDS

    smoke = runtime.run_text("asset-adapter smoke all", workspace=tmp_path, max_steps=3)
    assert smoke.plan[0].tool_name == "learning_asset_adapter_template_smoke"
    assert smoke.results[0].ok
    assert smoke.results[0].data["status"] == "pass"
    assert smoke.results[0].data["smoke_count"] == 5


def test_learning_asset_adapter_drill_activates_five_practical_learned_tools(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    result = runtime.run_text("asset-adapter drill", workspace=tmp_path, max_steps=20)
    expected_plan = [
        "learning_asset_adapter_guide",
        "learning_asset_adapter_template_list",
        "learning_asset_adapter_template_smoke",
        "learning_asset_adapter_drill",
        "learning_asset_activation_smoke",
        "runtime_tool_alignment_check",
        "runtime_llm_operational_drill",
    ]
    assert [step.tool_name for step in result.plan] == expected_plan
    assert all(item.ok for item in result.results)

    drill = result.results[3].data
    assert drill["status"] == "pass"
    assert drill["activated_count"] == 5
    assert {item["adapter_template_id"] for item in drill["activation_report"]["activated_assets"]} == EXPECTED_TEMPLATE_IDS
    assert drill["activation_smoke_report"]["status"] == "pass"
    assert drill["learned_tool_calls"]
    assert all(item["ok"] for item in drill["learned_tool_calls"])

    active_by_template = {
        item["adapter_template_id"]: item["tool_name"]
        for item in drill["activation_report"]["activated_assets"]
    }
    for template_id, tool_name in active_by_template.items():
        direct = runtime.execute_plan(
            [ToolInvocation(tool_name, dict(TEMPLATES[template_id].smoke_args))],
            workspace=tmp_path,
            user_message=f"direct R21 learned adapter {template_id}",
            max_steps=3,
        )
        assert direct.results[0].ok
        assert direct.results[0].data["status"] == "ok"
        assert direct.results[0].data["data"]["call_mode"] == "activated_candidate_adapter"
        assert direct.results[0].data["data"]["candidate_output"]["status"] == "ok"
