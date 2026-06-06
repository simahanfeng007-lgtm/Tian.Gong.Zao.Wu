from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tiangong_agent_runtime.execution_policy import RiskLevel
from tiangong_agent_runtime.plan_bridge import PlanBridge
from tiangong_agent_runtime.plan_schema import validate_and_build_plan
from tiangong_agent_runtime.planner_context_integration import (
    ExecutionStepDraft,
    PlannerContextIntegrationBridge,
    PlannerResumeEnvelope,
    UnifiedPlannerHint,
    stable_planner_context_digest,
)
from tiangong_agent_runtime.risk_classifier import RiskClassifier
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.tool_result import ToolResultStatus
from tiangong_agent_shell.tool_bridge import ToolExecutionMode

ROOT = Path(__file__).resolve().parents[1]


def test_l6_31_empty_bridge_is_shell_only() -> None:
    bridge = PlannerContextIntegrationBridge()
    snapshot = bridge.public_dict()
    assert snapshot["schema"] == "tiangong.l6_31.planner_context_integration.v1"
    assert snapshot["status"] == "empty"


def test_l6_31_builds_unified_planner_context_from_l6_24_to_l6_30_reports() -> None:
    bridge = PlannerContextIntegrationBridge()
    report = bridge.build(
        shell_mount_report={
            "schema": "tiangong.l6_24.shell_system_mount.v1",
            "status": "shell_mount_ready",
            "summary": "十八系统外壳挂载完成。",
            "systems": [
                {"system_id": "memory", "name": "记忆系统", "status": "active_shell_mounted"},
                {"system_id": "emotion", "name": "情志系统", "status": "partial_shell_mounted"},
            ],
        },
        project_repair_report={
            "schema": "tiangong.l6_25.project_repair_plan.v1",
            "status": "repair_plan_ready",
            "patch_plan": [
                {"step_id": "patch:demo", "operation": "minimal_patch", "risk_level": "A3", "rationale": "补最小外壳接线。"}
            ],
            "regression_hints": [
                {"name": "pytest:l6_31", "command": "pytest", "target": "tests/test_l6_31_planner_context_integration.py", "priority": "P0"}
            ],
            "rollback_evidence": {"status": "ready"},
        },
        delivery_standardization_report={
            "schema": "tiangong.l6_26.delivery_standardization.v1",
            "status": "delivery_standard_has_open_items",
            "change_set": [{"path": "tiangong_agent_runtime/planner_context_integration.py"}],
            "test_evidence": [{"test_ref": "compileall", "command": "compileall", "target": ".", "status": "pending"}],
            "todo_report": [{"item_id": "todo:full_pytest", "priority": "P2", "description": "完整 pytest 待跑。"}],
            "manifest_evidence": {"status": "planned", "manifest_available": True},
            "integrity_evidence": {"status": "planned", "report_digest": "demo"},
        },
        provider_adaptation_report={
            "schema": "tiangong.l6_27.provider_adaptation_shell.v1",
            "status": "provider_adaptation_shell_ready",
            "provider_profiles": [{"provider_id": "deepseek_v4"}],
            "api_surface_routes": [
                {
                    "provider_id": "deepseek_v4",
                    "surface_id": "chat_completions",
                    "route_kind": "plan_api",
                    "endpoint_ref": "provider:endpoint:deepseek",
                    "credential_scope_ref": "credential:runtime_ref",
                }
            ],
            "governance_mounts": [{"mount_ref": "provider:gated"}],
        },
        learning_convergence_report={
            "schema": "tiangong.l6_28.learning_convergence.v1",
            "status": "learning_convergence_ready",
            "planner_hint_routes": [{"route_ref": "hint:learning"}],
            "consumption_cards": [
                {"card_ref": "card:demo", "title": "消费外骨骼卡片", "immediate_next_action": "读取卡片后生成最小执行草案。"}
            ],
        },
        recovery_coordination_report={
            "schema": "tiangong.l6_29.recovery_coordination.v1",
            "status": "recovery_coordination_ready",
            "summary": "恢复协调外壳就绪。",
            "failure_signals": [{"error_code": "last_run_partial", "summary": "上一轮部分完成。"}],
            "resume_plans": [
                {"plan_ref": "resume:demo", "title": "续接执行", "next_action": "先消费 UnifiedPlannerContext，再执行最小 smoke。", "ordered_steps": ["读取上下文", "运行定向测试"]}
            ],
            "handoff_digests": [{"handoff_ref": "handoff:demo", "task_boundary": "仅交给下一轮 Planner。"}],
            "budget_updates": [{"budget_pool": "long_chain", "remaining_step_hint": 20, "continuation_policy": "continue"}],
        },
        governance_execution_report={
            "schema": "tiangong.l6_30.governance_execution.v1",
            "status": "governance_execution_ready",
            "summary": "治理执行力化就绪。",
            "fast_lanes": [
                {"lane_ref": "lane:a0_a3", "lane_name": "草案快车道", "risk_levels": ["A0", "A1", "A2", "A3"], "action_kinds": ["draft", "analysis", "smoke"], "planner_policy": "auto", "quality_gate_position": "before_release"}
            ],
            "boundaries": [
                {"boundary_ref": "boundary:a5", "boundary_name": "A5 硬边界", "trigger": "凭证读取或内核路径", "risk_level": "A5", "action": "阻断", "blocks_execution": True, "hard_boundary": True},
                {"boundary_ref": "boundary:release", "boundary_name": "发布门", "trigger": "正式发布/注册/激活", "risk_level": "A4", "action": "确认", "requires_confirmation": True, "release_or_activation_gate": True},
            ],
            "decisions": [
                {"decision_ref": "decision:fast", "source_ref": "lane:a0_a3", "risk_level": "A2", "action_kind": "draft", "status": "fast_pass_candidate", "planner_next": "继续最小草案。"},
                {"decision_ref": "decision:block", "source_ref": "boundary:a5", "risk_level": "A5", "action_kind": "secret", "status": "blocked", "reason": "凭证读取", "planner_next": "停止并重规划。"},
            ],
            "planner_hints": [{"hint_ref": "governance:hint", "title": "治理提示", "next_action": "A0-A4 快车道，A5 阻断。"}],
            "pending_confirmation_count": 1,
        },
        task_id="l6_31_demo",
        run_id="run_demo",
        notes="执行力第一，统一 Planner 上下文。",
    )
    payload = report.public_dict()
    ctx = payload["unified_context"]
    assert payload["schema"] == "tiangong.l6_31.planner_context_integration.v1"
    assert payload["status"] == "planner_context_ready"
    assert payload["execution_first"] is True
    assert payload["shell_only"] is True
    assert payload["planner_consumable"] is True
    assert payload["a0_a4_fast_lane_preserved"] is True
    assert payload["a5_hard_boundary_preserved"] is True
    assert payload["provider_declaration_only"] is True
    assert payload["budget_projection_only"] is True
    assert payload["recovery_projection_only"] is True
    assert payload["no_direct_execution"] is True
    assert payload["no_registry_mutation"] is True
    assert payload["no_kernel_mutation"] is True
    assert payload["no_secret_read"] is True
    assert payload["no_provider_call"] is True
    assert payload["invokes_tool"] is False
    assert payload["writes_file"] is False
    assert payload["applies_patch"] is False
    assert payload["registers_tool"] is False
    assert payload["registers_skill"] is False
    assert payload["touches_kernel"] is False
    assert payload["source_evidence_count"] == 7
    assert payload["planner_hint_count"] >= 5
    assert payload["next_execution_step_count"] >= 4
    assert payload["fast_lane_action_count"] >= 1
    assert payload["blocked_action_count"] >= 1
    assert payload["required_confirmation_count"] >= 1
    assert ctx["active_shell_system_count"] == 2
    assert ctx["task_id"] == "l6_31_demo"
    assert ctx["run_id"] == "run_demo"
    assert all(option["live_call_enabled"] is False for option in ctx["provider_surface_options"])
    assert all(not hint["fast_lane_candidate"] for hint in ctx["planner_hints"] if hint["risk_level"] == "A5")
    assert ctx["recovery_resume_plan"]["ready_for_next_run"] is True
    assert payload["report_digest"]
    assert stable_planner_context_digest(report) == payload["report_digest"]


def test_l6_31_forbids_mutating_or_executing_objects() -> None:
    try:
        UnifiedPlannerHint(
            hint_ref="hint:bad",
            source_ref="source:bad",
            title="bad",
            action_hint="bad",
            action_type="bad",
            invokes_tool=True,
        )
        raise AssertionError("UnifiedPlannerHint should reject tool invocation")
    except ValueError:
        pass
    try:
        UnifiedPlannerHint(
            hint_ref="hint:a5",
            source_ref="source:a5",
            title="bad",
            action_hint="bad",
            action_type="bad",
            risk_level="A5",
            blocks_execution=False,
        )
        raise AssertionError("UnifiedPlannerHint should reject non-blocking A5")
    except ValueError:
        pass
    try:
        ExecutionStepDraft(
            step_id="step:bad",
            title="bad",
            source_hint="hint:bad",
            action_type="bad",
            risk_level="A2",
            requires_confirmation=False,
            suggested_tool_or_shell="bad",
            expected_evidence="bad",
            fallback_or_rollback="bad",
            writes_file=True,
        )
        raise AssertionError("ExecutionStepDraft should reject writes")
    except ValueError:
        pass
    try:
        PlannerResumeEnvelope(
            resume_mode="bad",
            last_known_state="bad",
            spawns_agent=True,
        )
        raise AssertionError("PlannerResumeEnvelope should reject agent spawn")
    except ValueError:
        pass


def test_l6_31_runtime_builds_planner_context(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    runtime = RuntimeEntry()
    result = runtime.run_planner_context_build(
        workspace=tmp_path,
        notes="执行力第一，统一 Planner 接入。",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
    )
    assert result.results[-1].tool_name == "build_planner_context"
    assert result.results[-1].status is ToolResultStatus.OK
    snapshot = runtime.planner_context_snapshot()
    assert snapshot["schema"] == "tiangong.l6_31.planner_context_integration.v1"
    assert snapshot["status"] == "planner_context_ready"
    assert snapshot["planner_consumable"] is True
    assert snapshot["no_direct_execution"] is True
    assert snapshot["no_registry_mutation"] is True
    assert snapshot["no_kernel_mutation"] is True
    assert snapshot["no_secret_read"] is True
    assert snapshot["no_provider_call"] is True
    assert "L6.31 统一 Planner" in runtime._build_planner_context_hint()
    assert not (tmp_path / "provider_call.log").exists()
    assert not (tmp_path / "tool_registry.json").exists()
    assert not (tmp_path / "tiangong_kernel_mutation.log").exists()


def test_l6_31_tool_is_a2_and_registered() -> None:
    runtime = RuntimeEntry()
    names = {tool.name: tool.default_risk for tool in runtime.available_tools()}
    assert names["build_planner_context"] == "A2"
    risk, reason = RiskClassifier().classify(ToolInvocation("build_planner_context", {"notes": "统一 Planner"}))
    assert risk is RiskLevel.A2
    assert "L6.31" in reason
    assert "UnifiedPlannerContext" in reason
    assert "不执行" in reason
    assert "不注册" in reason
    assert "不改内核" in reason


def test_l6_31_plan_bridge_and_schema_allow_planner_context() -> None:
    plan = PlanBridge().build_plan("L6.31 统一 Planner 接入 / 执行主链收口")
    assert plan[-1].tool_name == "build_planner_context"
    assert "build_governance_execution" in [step.tool_name for step in plan]
    built = validate_and_build_plan(
        {
            "steps": [
                {
                    "tool_name": "build_planner_context",
                    "arguments": {"notes": "统一 Planner", "max_items": 99, "task_id": "l6_31"},
                }
            ]
        }
    )
    assert built[0].tool_name == "build_planner_context"
    assert built[0].arguments["max_items"] == 60
    assert built[0].arguments["task_id"] == "l6_31"


def test_l6_31_cli_planner_context_build_and_export(tmp_path: Path) -> None:
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
        input="/planner-context-build 执行力第一，统一 Planner 接入\n/planner-context\n/planner-context-save planner_context.json\n/exit\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "L6.31 统一 Planner" in proc.stdout
    exported = json.loads((tmp_path / "planner_context.json").read_text(encoding="utf-8"))
    assert exported["schema"] == "tiangong.l6_31.planner_context_integration.v1"
    assert exported["status"] == "planner_context_ready"
    assert exported["planner_consumable"] is True
    assert exported["no_direct_execution"] is True
    assert exported["touches_kernel"] is False


def test_l6_31_notes_are_redacted() -> None:
    runtime = RuntimeEntry()
    runtime.run_planner_context_build(
        notes="api_key=sk-test-secret token=abc password=123 authorization=Bearer xyz",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
    )
    text = json.dumps(runtime.planner_context_snapshot(), ensure_ascii=False)
    assert "sk-test-secret" not in text
    assert "token=abc" not in text
    assert "password=123" not in text
    assert "Bearer xyz" not in text
