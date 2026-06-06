from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tiangong_agent_runtime.execution_policy import RiskLevel
from tiangong_agent_runtime.learning_convergence import (
    LearningConvergenceBridge,
    PlannerHintRoute,
    SkillDraftRoute,
    ToolCandidateRoute,
    stable_learning_convergence_digest,
)
from tiangong_agent_runtime.plan_bridge import PlanBridge
from tiangong_agent_runtime.plan_schema import validate_and_build_plan
from tiangong_agent_runtime.risk_classifier import RiskClassifier
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.tool_result import ToolResultStatus
from tiangong_agent_shell.tool_bridge import ToolExecutionMode

ROOT = Path(__file__).resolve().parents[1]


def test_l6_28_empty_bridge_is_shell_only() -> None:
    bridge = LearningConvergenceBridge()
    snapshot = bridge.public_dict()
    assert snapshot["schema"] == "tiangong.l6_28.learning_convergence.v1"
    assert snapshot["status"] == "empty"


def test_l6_28_converges_sources_into_direct_consumption_cards() -> None:
    bridge = LearningConvergenceBridge()
    report = bridge.converge(
        experience_report={
            "schema": "tiangong.l6_20.experience_synthesis.v1",
            "status": "candidate_ready",
            "skill_candidates": [
                {
                    "candidate_ref": "skill_candidate:test",
                    "skill_name": "质量门失败快速修复",
                    "purpose": "先定位失败项，再生成修复顺序，避免反复询问。",
                    "trigger_hint": "质量门 fail 或 warn。",
                }
            ],
            "tool_gap_candidates": [
                {
                    "candidate_ref": "tool_gap:test",
                    "tool_gap_name": "minimal_quality_summary",
                    "capability_need": "把 pytest/compileall 输出压缩为可执行修复清单。",
                }
            ],
        },
        skill_queue_report={
            "schema": "tiangong.l6_21.skill_review_queue.v1",
            "status": "queue_ready",
            "draft_versions": [
                {
                    "draft_ref": "skill_draft:test",
                    "skill_name": "质量门失败快速修复",
                    "purpose": "先定位失败项，再生成修复顺序。",
                    "trigger_hint": "质量门失败。",
                }
            ],
        },
        tool_request_report={
            "schema": "tiangong.l6_22.tool_production_request.v1",
            "status": "request_ready",
            "production_requests": [
                {
                    "request_ref": "tool_request:test",
                    "tool_name_hint": "minimal_quality_summary",
                    "capability_need": "把质量检查输出压缩成修复清单。",
                }
            ],
        },
        exoskeleton_report={
            "schema": "tiangong.l6_23.execution_exoskeleton.v1",
            "status": "exoskeleton_ready",
            "planner_hints": [
                {
                    "hint_ref": "planner_hint:test",
                    "source_ref": "skill_draft:test",
                    "title": "质量门失败快速修复",
                    "trigger": "质量门失败。",
                    "action_hint": "先定位失败项，再生成修复顺序。",
                }
            ],
            "tool_candidate_tickets": [
                {
                    "ticket_ref": "tool_ticket:test",
                    "tool_name": "minimal_quality_summary",
                    "purpose": "把质量检查输出压缩成修复清单。",
                    "smoke_test": "create toy failing test -> parse summary -> assert repair list",
                }
            ],
        },
        notes="执行力第一，把沉淀结果变成 Planner 可消费卡片。",
    )
    payload = report.public_dict()
    assert payload["status"] == "learning_convergence_ready"
    assert payload["execution_first"] is True
    assert payload["direct_consumption"] is True
    assert payload["shell_only"] is True
    assert payload["learning_loop_closed"] is True
    assert payload["blocks_only_activation_release"] is True
    assert payload["planner_hint_count"] >= 1
    assert payload["skill_draft_count"] >= 1
    assert payload["tool_candidate_count"] >= 1
    assert payload["consumption_card_count"] >= 3
    assert payload["writes_memory"] is False
    assert payload["writes_skill_registry"] is False
    assert payload["registers_skill"] is False
    assert payload["activates_skill"] is False
    assert payload["produces_tool"] is False
    assert payload["writes_tool_code"] is False
    assert payload["registers_tool"] is False
    assert payload["releases_tool_handle"] is False
    assert payload["touches_kernel"] is False
    assert payload["report_digest"]
    assert stable_learning_convergence_digest(report) == payload["report_digest"]
    assert any("ExecutionConsumptionCard" not in item["immediate_next_action"] for item in payload["consumption_cards"])


def test_l6_28_forbids_activation_and_tool_side_effect_flags() -> None:
    try:
        PlannerHintRoute(
            route_ref="route:bad",
            source_ref="source:bad",
            title="bad",
            trigger="bad",
            action_hint="bad",
            activates_skill=True,
        )
        raise AssertionError("PlannerHintRoute should reject skill activation")
    except ValueError:
        pass
    try:
        SkillDraftRoute(
            route_ref="skill:bad",
            source_ref="source:bad",
            skill_name="bad",
            purpose="bad",
            next_use_condition="bad",
            planner_hint_ref="hint:bad",
            registers_skill=True,
        )
        raise AssertionError("SkillDraftRoute should reject skill registration")
    except ValueError:
        pass
    try:
        ToolCandidateRoute(
            route_ref="tool:bad",
            source_ref="source:bad",
            tool_name="bad",
            purpose="bad",
            smoke_test="bad",
            writes_tool_code=True,
        )
        raise AssertionError("ToolCandidateRoute should reject tool code writes")
    except ValueError:
        pass


def test_l6_28_runtime_builds_learning_convergence(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    result = runtime.run_learning_convergence_build(
        workspace=tmp_path,
        notes="执行力第一，把经验转成 Planner 可消费卡片，并推进最小工具草案 smoke。",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
    )
    assert result.results[-1].tool_name == "build_learning_convergence"
    assert result.results[-1].status is ToolResultStatus.OK
    snapshot = runtime.learning_convergence_snapshot()
    assert snapshot["schema"] == "tiangong.l6_28.learning_convergence.v1"
    assert snapshot["status"] == "learning_convergence_ready"
    assert snapshot["direct_consumption"] is True
    assert snapshot["planner_hint_count"] >= 1
    assert snapshot["consumption_card_count"] >= 1
    assert "direct_consumption=True" in runtime._build_planner_context_hint()
    assert not (tmp_path / "skill_registry.json").exists()
    assert not (tmp_path / "tool_registry.json").exists()


def test_l6_28_tool_is_a2_and_registered() -> None:
    runtime = RuntimeEntry()
    names = {tool.name: tool.default_risk for tool in runtime.available_tools()}
    assert names["build_learning_convergence"] == "A2"
    risk, reason = RiskClassifier().classify(ToolInvocation("build_learning_convergence", {"notes": "合流"}))
    assert risk is RiskLevel.A2
    assert "L6.28" in reason
    assert "不写记忆" in reason
    assert "不注册 Skill" in reason
    assert "不生产 Tool" in reason


def test_l6_28_plan_bridge_and_schema_allow_learning_convergence() -> None:
    plan = PlanBridge().build_plan("经验合流 执行力第一，把 Skill/Tool 候选变成 Planner 卡片")
    assert [step.tool_name for step in plan] == [
        "synthesize_experience_candidates",
        "queue_skill_candidates",
        "queue_tool_production_requests",
        "build_execution_exoskeleton",
        "build_learning_convergence",
    ]
    built = validate_and_build_plan(
        {
            "steps": [
                {
                    "tool_name": "build_learning_convergence",
                    "arguments": {"notes": "执行合流", "max_items": 18},
                }
            ]
        }
    )
    assert built[0].tool_name == "build_learning_convergence"
    assert built[0].arguments["max_items"] == 18


def test_l6_28_cli_learning_converge_build_and_export(tmp_path: Path) -> None:
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
        input="/learning-converge-build 执行力第一，把经验 Skill Tool 合流\n/learning-converge\n/learning-converge-save learning_convergence.json\n/exit\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "L6.28 执行合流" in proc.stdout
    exported = json.loads((tmp_path / "learning_convergence.json").read_text(encoding="utf-8"))
    assert exported["schema"] == "tiangong.l6_28.learning_convergence.v1"
    assert exported["status"] == "learning_convergence_ready"
    assert exported["direct_consumption"] is True
    assert exported["writes_memory"] is False
    assert exported["writes_skill_registry"] is False
    assert exported["produces_tool"] is False
    assert exported["registers_tool"] is False
    assert exported["touches_kernel"] is False


def test_l6_28_notes_are_redacted() -> None:
    runtime = RuntimeEntry()
    runtime.run_learning_convergence_build(
        notes="api_key=sk-test-secret token=abc password=123 authorization=Bearer xyz",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
    )
    text = json.dumps(runtime.learning_convergence_snapshot(), ensure_ascii=False)
    assert "sk-test-secret" not in text
    assert "token=abc" not in text
    assert "password=123" not in text
    assert "Bearer xyz" not in text


def test_l6_28_runtime_does_not_pollute_kernel_import_direction() -> None:
    kernel_root = ROOT / "tiangong_kernel"
    forbidden = [
        "learning_convergence",
        "build_learning_convergence",
        "LearningConvergenceBridge",
        "/learning-converge",
    ]
    offenders: list[str] = []
    for path in kernel_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)}::{token}")
    assert offenders == []
