from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tiangong_agent_runtime.execution_policy import RiskLevel
from tiangong_agent_runtime.plan_bridge import PlanBridge
from tiangong_agent_runtime.plan_schema import validate_and_build_plan
from tiangong_agent_runtime.recovery_coordination import (
    HandoffDigest,
    RecoveryCoordinationBridge,
    RepairCandidate,
    ResumePlan,
    stable_recovery_coordination_digest,
)
from tiangong_agent_runtime.risk_classifier import RiskClassifier
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.tool_result import ToolResultStatus
from tiangong_agent_shell.tool_bridge import ToolExecutionMode

ROOT = Path(__file__).resolve().parents[1]


def test_l6_29_empty_bridge_is_shell_only() -> None:
    bridge = RecoveryCoordinationBridge()
    snapshot = bridge.public_dict()
    assert snapshot["schema"] == "tiangong.l6_29.recovery_coordination.v1"
    assert snapshot["status"] == "empty"


def test_l6_29_builds_failure_repair_handoff_budget_resume_path() -> None:
    bridge = RecoveryCoordinationBridge()
    report = bridge.build(
        diagnosis_report={
            "schema": "tiangong.l6_17.engineering_diagnosis.v1",
            "status": "needs_repair",
            "issues": [
                {
                    "code": "quality_check_failed",
                    "severity": "P1",
                    "message": "compileall 失败，需要最小修复。",
                    "suggested_actions": ["读取失败文件", "最小补丁", "复测"],
                }
            ],
        },
        quality_gate_report={
            "schema": "tiangong.l6_18.quality_gate.v1",
            "decision": "fail",
            "issues": [
                {
                    "code": "quality_check_failed",
                    "severity": "P1",
                    "message": "pytest 失败，禁止发布。",
                }
            ],
        },
        project_repair_report={
            "schema": "tiangong.l6_25.project_repair_plan.v1",
            "status": "repair_plan_ready",
            "patch_plan": [
                {
                    "phase": "repair",
                    "target_path": "tiangong_agent_runtime/demo.py",
                    "operation": "minimal_patch",
                    "risk_level": "A3_when_applied",
                }
            ],
            "regression_hints": [{"command": "compileall", "target": "."}],
        },
        learning_convergence_report={
            "schema": "tiangong.l6_28.learning_convergence.v1",
            "status": "learning_convergence_ready",
            "consumption_cards": [
                {"immediate_next_action": "先定位失败项，生成最小补丁，然后 compileall 复测。"}
            ],
        },
        notes="执行力第一，把失败压成恢复路径。",
        step_budget=20,
    )
    payload = report.public_dict()
    assert payload["status"] == "recovery_coordination_ready"
    assert payload["execution_first"] is True
    assert payload["shell_only"] is True
    assert payload["recovery_path_ready"] is True
    assert payload["multi_agent_projection_only"] is True
    assert payload["budget_projection_only"] is True
    assert payload["uses_runtime_governance"] is True
    assert payload["failure_signal_count"] >= 1
    assert payload["repair_candidate_count"] >= 1
    assert payload["handoff_digest_count"] >= 1
    assert payload["budget_update_count"] == 1
    assert payload["resume_plan_count"] >= 1
    assert payload["spawns_agent"] is False
    assert payload["invokes_tool"] is False
    assert payload["applies_patch"] is False
    assert payload["writes_file"] is False
    assert payload["mutates_budget"] is False
    assert payload["registers_tool"] is False
    assert payload["registers_skill"] is False
    assert payload["modifies_kernel"] is False
    assert payload["report_digest"]
    assert stable_recovery_coordination_digest(report) == payload["report_digest"]
    assert all(item["spawn_now"] is False for item in payload["handoff_digests"])
    assert all(item["mutates_budget"] is False for item in payload["budget_updates"])


def test_l6_29_forbids_side_effect_flags() -> None:
    try:
        RepairCandidate(
            candidate_ref="repair:bad",
            failure_ref="failure:bad",
            title="bad",
            priority="P1",
            planner_hint="bad",
            applies_patch_now=True,
        )
        raise AssertionError("RepairCandidate should reject direct patch application")
    except ValueError:
        pass
    try:
        HandoffDigest(
            handoff_ref="handoff:bad",
            failure_ref="failure:bad",
            suggested_role="bad",
            task_boundary="bad",
            input_summary="bad",
            expected_output="bad",
            parent_resume_contract="bad",
            spawn_now=True,
        )
        raise AssertionError("HandoffDigest should reject immediate agent spawn")
    except ValueError:
        pass
    try:
        ResumePlan(
            plan_ref="resume:bad",
            title="bad",
            next_action="bad",
            direct_execution_now=True,
        )
        raise AssertionError("ResumePlan should reject direct execution")
    except ValueError:
        pass


def test_l6_29_runtime_builds_recovery_coordination(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    runtime = RuntimeEntry()
    result = runtime.run_recovery_coordination_build(
        workspace=tmp_path,
        notes="执行力第一，失败后生成恢复候选、handoff 摘要、预算更新和续接计划。",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
    )
    assert result.results[-1].tool_name == "build_recovery_coordination"
    assert result.results[-1].status is ToolResultStatus.OK
    snapshot = runtime.recovery_coordination_snapshot()
    assert snapshot["schema"] == "tiangong.l6_29.recovery_coordination.v1"
    assert snapshot["status"] == "recovery_coordination_ready"
    assert snapshot["resume_plan_count"] >= 1
    assert snapshot["budget_projection_only"] is True
    assert "L6.29 恢复协调" in runtime._build_planner_context_hint()
    assert not (tmp_path / "subagent_spawn.log").exists()
    assert not (tmp_path / "budget_mutation.json").exists()


def test_l6_29_tool_is_a2_and_registered() -> None:
    runtime = RuntimeEntry()
    names = {tool.name: tool.default_risk for tool in runtime.available_tools()}
    assert names["build_recovery_coordination"] == "A2"
    risk, reason = RiskClassifier().classify(ToolInvocation("build_recovery_coordination", {"notes": "恢复协调"}))
    assert risk is RiskLevel.A2
    assert "L6.29" in reason
    assert "不派生子智能体" in reason
    assert "不执行补丁" in reason
    assert "不改预算" in reason


def test_l6_29_plan_bridge_and_schema_allow_recovery_coordination() -> None:
    plan = PlanBridge().build_plan("恢复协调 执行力第一，自修复 多智能体 预算联动")
    assert [step.tool_name for step in plan] == ["build_learning_convergence", "build_recovery_coordination"]
    built = validate_and_build_plan(
        {
            "steps": [
                {
                    "tool_name": "build_recovery_coordination",
                    "arguments": {"notes": "恢复协调", "max_items": 12, "step_budget": 20},
                }
            ]
        }
    )
    assert built[0].tool_name == "build_recovery_coordination"
    assert built[0].arguments["max_items"] == 12
    assert built[0].arguments["step_budget"] == 20


def test_l6_29_cli_recovery_build_and_export(tmp_path: Path) -> None:
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
        input="/recovery-build 执行力第一，生成恢复续接路径\n/recovery\n/recovery-save recovery_coordination.json\n/exit\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "L6.29 恢复协调" in proc.stdout
    exported = json.loads((tmp_path / "recovery_coordination.json").read_text(encoding="utf-8"))
    assert exported["schema"] == "tiangong.l6_29.recovery_coordination.v1"
    assert exported["status"] == "recovery_coordination_ready"
    assert exported["spawns_agent"] is False
    assert exported["applies_patch"] is False
    assert exported["mutates_budget"] is False
    assert exported["modifies_kernel"] is False


def test_l6_29_notes_are_redacted() -> None:
    runtime = RuntimeEntry()
    runtime.run_recovery_coordination_build(
        notes="api_key=sk-test-secret token=abc password=123 authorization=Bearer xyz",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
    )
    text = json.dumps(runtime.recovery_coordination_snapshot(), ensure_ascii=False)
    assert "sk-test-secret" not in text
    assert "token=abc" not in text
    assert "password=123" not in text
    assert "Bearer xyz" not in text


def test_l6_29_runtime_does_not_pollute_kernel_import_direction() -> None:
    kernel_root = ROOT / "tiangong_kernel"
    forbidden = [
        "recovery_coordination",
        "build_recovery_coordination",
        "RecoveryCoordinationBridge",
        "/recovery-build",
    ]
    offenders: list[str] = []
    for path in kernel_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)}::{token}")
    assert offenders == []
