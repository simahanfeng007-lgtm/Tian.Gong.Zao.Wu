from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tiangong_agent_runtime.execution_policy import RiskLevel
from tiangong_agent_runtime.p0_system_integration import (
    L6_38_SCHEMA,
    ChainBudgetLease,
    CredentialRef,
    L638P0SystemIntegrationBridge,
    ProviderExecutionTicket,
    ProviderProfile,
    SkillActivationIntent,
    StepBudgetLedger,
    SubtaskTicket,
)
from tiangong_agent_runtime.plan_bridge import PlanBridge
from tiangong_agent_runtime.plan_schema import validate_and_build_plan
from tiangong_agent_runtime.risk_classifier import RiskClassifier
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.tool_result import ToolResultStatus
from tiangong_agent_shell.tool_bridge import ToolExecutionMode

ROOT = Path(__file__).resolve().parents[1]


def _workspace(tmp_path: Path) -> Path:
    (tmp_path / "README.md").write_text("# demo\n", encoding="utf-8")
    return tmp_path


def test_l6_38_bridge_builds_provider_budget_skill_handoff_report_without_side_effects() -> None:
    bridge = L638P0SystemIntegrationBridge()
    bridge.build_provider(notes="api_key=sk-test token=abc secret=hidden")
    bridge.build_budget(max_steps=10, planned_steps=4, notes="budget smoke")
    bridge.build_skill(notes="把执行链经验沉淀为候选 Skill", max_items=2)
    bridge.build_handoff(parent_chain_id="parent:l6_38", notes="拆分 Provider Budget Skill Handoff", max_subtasks=3)
    report = bridge.build_report().public_dict()

    assert report["schema"] == L6_38_SCHEMA
    assert report["status"] == "p0_systems_ready"
    assert report["planner_consumable"] is True
    assert report["runtime_governed"] is True
    assert report["uses_planner_execution_controller"] is True
    assert report["no_second_runtime"] is True
    assert report["no_kernel_mutation"] is True
    assert report["no_provider_sdk_call"] is True
    assert report["no_plain_secret"] is True
    assert report["no_skill_activation"] is True
    assert report["no_auto_recursive_handoff"] is True
    assert report["no_direct_budget_mutation"] is True
    assert report["provider"]["execution_tickets"][0]["credential_plaintext_read"] is False
    assert report["budget"]["mutates_budget"] is False
    assert report["skill"]["activates_skill"] is False
    assert report["handoff"]["no_auto_recursive_spawn"] is True

    rendered = json.dumps(report, ensure_ascii=False).lower()
    assert "sk-test" not in rendered
    assert "token=abc" not in rendered
    assert "secret=hidden" not in rendered


def test_l6_38_boundary_dataclasses_reject_bypass_flags() -> None:
    with pytest.raises(ValueError):
        CredentialRef(ref_id="credential_ref:bad", provider_id="deepseek_v4", read_attempted=True)
    with pytest.raises(ValueError):
        ProviderProfile(
            provider_id="deepseek_v4",
            display_name="DeepSeek",
            default_model_id="deepseek-v4",
            plugin_sdk_call_allowed=True,
        )
    with pytest.raises(ValueError):
        ProviderExecutionTicket(
            ticket_id="ticket:bad",
            provider_id="deepseek_v4",
            profile_ref="provider_profile:deepseek_v4",
            credential_ref=CredentialRef(ref_id="credential_ref:deepseek", provider_id="deepseek_v4"),
            imports_provider_sdk=True,
        )
    with pytest.raises(ValueError):
        StepBudgetLedger(ledger_id="ledger:bad", max_steps=10, planned_steps=1, blocks_a0_to_a4_by_default=True)
    with pytest.raises(ValueError):
        ChainBudgetLease(
            lease_id="lease:bad",
            owner_chain_id="chain",
            current_limit=10,
            requested_extension=5,
            mutates_budget=True,
        )
    with pytest.raises(ValueError):
        SkillActivationIntent(
            intent_id="intent:bad",
            ticket_id="review:bad",
            target_skill_name="skill:bad",
            formal_activation_allowed_now=True,
        )
    with pytest.raises(ValueError):
        SubtaskTicket(
            ticket_id="subtask:bad",
            parent_chain_id="parent",
            subtask_title="bad",
            payload_summary="bad",
            auto_spawn_allowed=True,
        )


def test_l6_38_runtime_registers_tools_and_executes_through_l6_37_chain(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    tools = {tool.name: tool.default_risk for tool in runtime.available_tools()}
    expected = {
        "build_l6_38_provider_integration",
        "build_l6_38_budget_snapshot",
        "build_l6_38_skill_integration",
        "build_l6_38_handoff_integration",
        "build_l6_38_p0_integration",
    }
    assert expected.issubset(set(tools))
    assert all(tools[name] == "A2" for name in expected)

    result = runtime.run_l6_38_p0_system_integration(
        workspace=_workspace(tmp_path),
        notes="L6.38 Provider / Budget / Skill / Handoff",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps=10,
        max_items=4,
    )
    assert result.results[-1].tool_name == "build_l6_38_p0_integration"
    assert result.results[-1].status is ToolResultStatus.OK
    report = runtime.p0_system_integration_snapshot()
    assert report["schema"] == L6_38_SCHEMA
    assert report["status"] == "p0_systems_ready"
    assert report["uses_planner_execution_controller"] is True

    planner = runtime.planner_execution_snapshot()
    assert planner["status"] == "completed"
    assert planner["uses_long_chain_runner"] is True
    assert planner["uses_execution_spine"] is True
    assert planner["no_parallel_runtime"] is True
    assert planner["no_direct_adapter_call"] is True
    assert planner["no_kernel_mutation"] is True
    executed_tools = {step["tool_name"] for step in planner["step_records"]}
    assert expected.issubset(executed_tools)


def test_l6_38_plan_bridge_schema_and_risk_classifier_accept_p0_tools() -> None:
    plan = PlanBridge().build_plan("L6.38 Provider / Budget / Skill / Handoff 系统接入")
    tool_names = [step.tool_name for step in plan]
    assert "build_l6_38_provider_integration" in tool_names
    assert "build_l6_38_budget_snapshot" in tool_names
    assert "build_l6_38_skill_integration" in tool_names
    assert "build_l6_38_handoff_integration" in tool_names
    assert "build_l6_38_p0_integration" in tool_names

    validated = validate_and_build_plan(
        {
            "steps": [
                {"tool_name": "l6_38_provider", "arguments": {"requested_call_mode": "sample_replay"}},
                {"tool_name": "l6_38_budget", "arguments": {"max_steps": 10, "planned_steps": 3}},
                {"tool_name": "l6_38_skill", "arguments": {"max_items": 2}},
                {"tool_name": "l6_38_handoff", "arguments": {"parent_chain_id": "parent:l6_38"}},
                {"tool_name": "l6_38_p0", "arguments": {}},
            ]
        }
    )
    assert [step.tool_name for step in validated] == [
        "build_l6_38_provider_integration",
        "build_l6_38_budget_snapshot",
        "build_l6_38_skill_integration",
        "build_l6_38_handoff_integration",
        "build_l6_38_p0_integration",
    ]

    classifier = RiskClassifier()
    for name in [step.tool_name for step in validated]:
        risk, reason = classifier.classify(ToolInvocation(name, {}))
        assert risk is RiskLevel.A2
        assert "L6.38" in reason


def test_l6_38_cli_build_show_export_and_reset(tmp_path: Path) -> None:
    _workspace(tmp_path)
    proc = subprocess.run(
        [sys.executable, "run_agent.py", "--mock", "--tool-mode", "runtime_governed", "--workspace", str(tmp_path)],
        cwd=ROOT,
        input="/p0-system-build L6.38 Provider Budget Skill Handoff\n/p0-system\n/p0-system-save p0_system.json\n/p0-system-reset\n/p0-system\n/exit\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "L6.38 P0 系统接入报告" in proc.stdout
    assert "L6.38 P0 系统接入报告已导出" in proc.stdout
    assert "L6.38 P0 系统接入报告已清空" in proc.stdout
    payload = json.loads((tmp_path / "p0_system.json").read_text(encoding="utf-8"))
    assert payload["schema"] == L6_38_SCHEMA
    assert payload["status"] == "p0_systems_ready"


def test_l6_38_does_not_pollute_kernel_layer() -> None:
    forbidden = {
        "p0_system_integration",
        "build_l6_38_provider_integration",
        "build_l6_38_budget_snapshot",
        "build_l6_38_skill_integration",
        "build_l6_38_handoff_integration",
        "build_l6_38_p0_integration",
        "/p0-system",
    }
    offenders: list[str] = []
    for path in (ROOT / "tiangong_kernel").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)}:{token}")
    assert offenders == []
