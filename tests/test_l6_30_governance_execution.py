from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tiangong_agent_runtime.execution_policy import RiskLevel
from tiangong_agent_runtime.governance_execution import (
    GovernanceBoundary,
    GovernanceDecisionDraft,
    GovernanceExecutionBridge,
    GovernanceFastLane,
    stable_governance_execution_digest,
)
from tiangong_agent_runtime.plan_bridge import PlanBridge
from tiangong_agent_runtime.plan_schema import validate_and_build_plan
from tiangong_agent_runtime.risk_classifier import RiskClassifier
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.tool_result import ToolResultStatus
from tiangong_agent_shell.tool_bridge import ToolExecutionMode

ROOT = Path(__file__).resolve().parents[1]


def test_l6_30_empty_bridge_is_shell_only() -> None:
    bridge = GovernanceExecutionBridge()
    snapshot = bridge.public_dict()
    assert snapshot["schema"] == "tiangong.l6_30.governance_execution.v1"
    assert snapshot["status"] == "empty"


def test_l6_30_builds_a0_a4_fast_lanes_and_a5_boundaries() -> None:
    bridge = GovernanceExecutionBridge()
    report = bridge.build(
        recovery_report={
            "schema": "tiangong.l6_29.recovery_coordination.v1",
            "status": "recovery_coordination_ready",
            "resume_plans": [
                {"plan_ref": "resume:test", "next_action": "按恢复候选生成最小补丁计划，执行前置检查，然后复测。"}
            ],
        },
        learning_convergence_report={
            "schema": "tiangong.l6_28.learning_convergence.v1",
            "status": "learning_convergence_ready",
            "consumption_cards": [
                {"card_ref": "card:test", "immediate_next_action": "消费 Planner 卡片，生成最小 smoke。"}
            ],
        },
        provider_adaptation_report={"schema": "tiangong.l6_27.provider_adaptation_shell.v1", "status": "provider_adaptation_ready"},
        delivery_standardization_report={"schema": "tiangong.l6_26.delivery_standardization.v1", "status": "delivery_standardization_ready"},
        project_repair_report={"schema": "tiangong.l6_25.project_repair_plan.v1", "status": "repair_plan_ready"},
        shell_mount_report={"schema": "tiangong.l6_24.shell_system_mount.v1", "status": "shell_mount_ready"},
        pending_confirmations=[{"ticket_id": "confirm_demo", "risk_level": "A4"}],
        notes="执行力第一，治理变护栏。",
    )
    payload = report.public_dict()
    assert payload["status"] == "governance_execution_ready"
    assert payload["execution_first"] is True
    assert payload["shell_only"] is True
    assert payload["a0_a4_fast_lane"] is True
    assert payload["a5_hard_boundary"] is True
    assert payload["release_activation_gated"] is True
    assert payload["quality_gate_only_blocks_release"] is True
    assert payload["no_policy_mutation"] is True
    assert payload["no_direct_execution"] is True
    assert payload["no_registry_mutation"] is True
    assert payload["no_kernel_mutation"] is True
    assert payload["fast_lane_count"] >= 4
    assert payload["hard_boundary_count"] >= 1
    assert payload["release_gate_count"] >= 1
    assert payload["decision_count"] >= 1
    assert payload["planner_hint_count"] >= 1
    assert payload["pending_confirmation_count"] == 1
    assert payload["modifies_policy"] is False
    assert payload["invokes_tool"] is False
    assert payload["writes_file"] is False
    assert payload["applies_patch"] is False
    assert payload["mutates_budget"] is False
    assert payload["registers_tool"] is False
    assert payload["registers_skill"] is False
    assert payload["touches_kernel"] is False
    assert payload["report_digest"]
    assert stable_governance_execution_digest(report) == payload["report_digest"]
    assert any("A0" in lane["risk_levels"] and "A4" not in lane["risk_levels"] for lane in payload["fast_lanes"])
    assert any(item["hard_boundary"] is True and item["risk_level"] == "A5" for item in payload["boundaries"])


def test_l6_30_forbids_policy_mutation_and_bad_boundaries() -> None:
    try:
        GovernanceFastLane(
            lane_ref="lane:bad",
            lane_name="bad",
            risk_levels=("A5",),
            action_kinds=("bad",),
            planner_policy="bad",
            quality_gate_position="bad",
        )
        raise AssertionError("GovernanceFastLane should reject A5")
    except ValueError:
        pass
    try:
        GovernanceBoundary(
            boundary_ref="boundary:bad",
            boundary_name="bad",
            trigger="bad",
            risk_level="A5",
            action="bad",
            blocks_execution=False,
            hard_boundary=True,
        )
        raise AssertionError("GovernanceBoundary should reject non-blocking hard boundary")
    except ValueError:
        pass
    try:
        GovernanceDecisionDraft(
            decision_ref="decision:bad",
            source_ref="source:bad",
            tool_or_action="bad",
            risk_level="A2",
            action_kind="bad",
            lane_ref="lane:bad",
            status="fast_pass_candidate",
            reason="bad",
            planner_next="bad",
            mutates_policy=True,
        )
        raise AssertionError("GovernanceDecisionDraft should reject policy mutation")
    except ValueError:
        pass


def test_l6_30_runtime_builds_governance_execution(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    runtime = RuntimeEntry()
    result = runtime.run_governance_execution_build(
        workspace=tmp_path,
        notes="执行力第一，A0-A4 快车道，A5 硬边界。",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
    )
    assert result.results[-1].tool_name == "build_governance_execution"
    assert result.results[-1].status is ToolResultStatus.OK
    snapshot = runtime.governance_execution_snapshot()
    assert snapshot["schema"] == "tiangong.l6_30.governance_execution.v1"
    assert snapshot["status"] == "governance_execution_ready"
    assert snapshot["a0_a4_fast_lane"] is True
    assert snapshot["a5_hard_boundary"] is True
    assert snapshot["no_policy_mutation"] is True
    assert "L6.30 治理执行力化" in runtime._build_planner_context_hint()
    assert not (tmp_path / "policy_mutation.json").exists()
    assert not (tmp_path / "tiangong_kernel_mutation.log").exists()


def test_l6_30_tool_is_a2_and_registered() -> None:
    runtime = RuntimeEntry()
    names = {tool.name: tool.default_risk for tool in runtime.available_tools()}
    assert names["build_governance_execution"] == "A2"
    risk, reason = RiskClassifier().classify(ToolInvocation("build_governance_execution", {"notes": "治理执行力化"}))
    assert risk is RiskLevel.A2
    assert "L6.30" in reason
    assert "A0-A4" in reason
    assert "A5" in reason
    assert "不改" in reason


def test_l6_30_plan_bridge_and_schema_allow_governance_execution() -> None:
    plan = PlanBridge().build_plan("治理执行力化 A0-A4 快车道 A5 硬边界")
    assert [step.tool_name for step in plan] == ["build_recovery_coordination", "build_governance_execution"]
    built = validate_and_build_plan(
        {
            "steps": [
                {
                    "tool_name": "build_governance_execution",
                    "arguments": {"notes": "治理执行力化", "max_items": 12},
                }
            ]
        }
    )
    assert built[0].tool_name == "build_governance_execution"
    assert built[0].arguments["max_items"] == 12


def test_l6_30_cli_governance_build_and_export(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            "run_agent.py",
            "--mock",
            "--tool-mode",
            "runtime_governed",
            "--workspace",
            str(tmp_path),
        ],
        cwd=ROOT,
        input="/governance-build 执行力第一，治理变护栏\n/governance\n/governance-save governance_execution.json\n/exit\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "L6.30 治理执行力化" in proc.stdout
    exported = json.loads((tmp_path / "governance_execution.json").read_text(encoding="utf-8"))
    assert exported["schema"] == "tiangong.l6_30.governance_execution.v1"
    assert exported["status"] == "governance_execution_ready"
    assert exported["a0_a4_fast_lane"] is True
    assert exported["a5_hard_boundary"] is True
    assert exported["no_policy_mutation"] is True
    assert exported["touches_kernel"] is False


def test_l6_30_notes_are_redacted() -> None:
    runtime = RuntimeEntry()
    runtime.run_governance_execution_build(
        notes="api_key=sk-test-secret token=abc password=123 authorization=Bearer xyz",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
    )
    text = json.dumps(runtime.governance_execution_snapshot(), ensure_ascii=False)
    assert "sk-test-secret" not in text
    assert "token=abc" not in text
    assert "password=123" not in text
    assert "Bearer xyz" not in text
