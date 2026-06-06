from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tiangong_agent_runtime.execution_exoskeleton import (
    ExecutionExoskeletonBridge,
    PlannerExecutionHint,
    ToolCandidateTicket,
)
from tiangong_agent_runtime.plan_bridge import PlanBridge
from tiangong_agent_runtime.plan_schema import validate_and_build_plan
from tiangong_agent_runtime.risk_classifier import RiskClassifier
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.tool_result import ToolResultStatus
from tiangong_agent_runtime.execution_policy import RiskLevel
from tiangong_agent_shell.tool_bridge import ToolExecutionMode

ROOT = Path(__file__).resolve().parents[1]


def test_l6_23_empty_bridge_is_lightweight_exoskeleton() -> None:
    bridge = ExecutionExoskeletonBridge()
    snapshot = bridge.public_dict()
    assert snapshot["schema"] == "tiangong.l6_23.execution_exoskeleton.v1"
    assert snapshot["status"] == "empty"


def test_l6_23_compresses_skill_and_tool_sources_into_short_chain() -> None:
    bridge = ExecutionExoskeletonBridge()
    report = bridge.compress(
        experience_report={
            "schema": "tiangong.l6_20.experience_synthesis.v1",
            "skill_candidates": [
                {
                    "candidate_ref": "skill_candidate:test",
                    "skill_name": "质量门失败快速修复",
                    "purpose": "先定位失败项，再直接生成修复顺序，避免反复询问。",
                    "trigger_hint": "质量门 failed 或 warn。",
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
        notes="执行力第一，压缩候选链。",
    )
    payload = report.public_dict()
    assert payload["status"] == "exoskeleton_ready"
    assert payload["strategy"] == "llm_execution_exoskeleton"
    assert payload["execution_first"] is True
    assert payload["minimal_chain"] is True
    assert payload["draft_only"] is True
    assert payload["planner_hints"]
    assert payload["tool_candidate_tickets"]
    assert payload["tool_candidate_tickets"][0]["max_spec_fields"] <= 7
    assert payload["tool_candidate_tickets"][0]["registers_tool"] is False
    assert payload["planner_hints"][0]["activates_skill"] is False


def test_l6_23_forbids_activation_and_real_tool_side_effect_flags() -> None:
    try:
        PlannerExecutionHint(
            hint_ref="hint:bad",
            source_ref="source:bad",
            title="bad",
            trigger="bad",
            action_hint="bad",
            activates_skill=True,
        )
        raise AssertionError("PlannerExecutionHint should reject skill activation")
    except ValueError:
        pass
    try:
        ToolCandidateTicket(
            ticket_ref="ticket:bad",
            source_ref="source:bad",
            tool_name="bad",
            purpose="bad",
            registers_tool=True,
        )
        raise AssertionError("ToolCandidateTicket should reject tool registration")
    except ValueError:
        pass


def test_l6_23_runtime_builds_exoskeleton_from_notes(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    result = runtime.run_exoskeleton_build(
        workspace=tmp_path,
        notes="重复发布时要把质量门失败经验转成 PlannerHint，并给出最小 Tool 票据。",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
    )
    assert result.results[-1].status is ToolResultStatus.OK
    snapshot = runtime.exoskeleton_snapshot()
    assert snapshot["schema"] == "tiangong.l6_23.execution_exoskeleton.v1"
    assert snapshot["status"] == "exoskeleton_ready"
    assert snapshot["planner_hints"]
    assert snapshot["tool_candidate_tickets"]
    assert "质量门只卡正式注册" in "\n".join(snapshot["next_actions"])


def test_l6_23_tool_is_a2_and_registered() -> None:
    runtime = RuntimeEntry()
    names = {tool.name: tool.default_risk for tool in runtime.available_tools()}
    assert names["build_execution_exoskeleton"] == "A2"
    risk, reason = RiskClassifier().classify(ToolInvocation("build_execution_exoskeleton", {"notes": "外骨骼"}))
    assert risk is RiskLevel.A2
    assert "外骨骼" in reason
    assert "不注册" in reason


def test_l6_23_plan_bridge_and_schema_allow_exoskeleton() -> None:
    plan = PlanBridge().build_plan("外骨骼 把技能和工具候选压缩成执行提示")
    assert [step.tool_name for step in plan] == [
        "synthesize_experience_candidates",
        "queue_skill_candidates",
        "queue_tool_production_requests",
        "build_execution_exoskeleton",
    ]
    built = validate_and_build_plan(
        {
            "steps": [
                {
                    "tool_name": "build_execution_exoskeleton",
                    "arguments": {"notes": "压缩候选链", "max_items": 3},
                }
            ]
        }
    )
    assert built[0].tool_name == "build_execution_exoskeleton"
    assert built[0].arguments["max_items"] == 3


def test_l6_23_cli_exoskeleton_build_and_export(tmp_path: Path) -> None:
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
        input="/exoskeleton-build 执行力第一，把候选链压缩成外骨骼\n/exoskeleton\n/exoskeleton-save exoskeleton.json\n/exit\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "LLM 外骨骼" in proc.stdout
    exported = json.loads((tmp_path / "exoskeleton.json").read_text(encoding="utf-8"))
    assert exported["schema"] == "tiangong.l6_23.execution_exoskeleton.v1"
    assert exported["minimal_chain"] is True
    assert exported["registers_tool"] is False
    assert exported["activates_skill"] is False


def test_l6_23_runtime_does_not_pollute_kernel_import_direction() -> None:
    kernel_root = ROOT / "tiangong_kernel"
    forbidden = ["execution_exoskeleton", "build_execution_exoskeleton", "ToolCandidateTicket", "/exoskeleton"]
    offenders: list[str] = []
    for path in kernel_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)}::{token}")
    assert offenders == []
