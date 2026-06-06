from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tiangong_agent_runtime.execution_policy import RiskLevel
from tiangong_agent_runtime.experience_synthesis import ExperienceSynthesisBridge
from tiangong_agent_runtime.plan_bridge import PlanBridge
from tiangong_agent_runtime.plan_schema import validate_and_build_plan
from tiangong_agent_runtime.risk_classifier import RiskClassifier
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.skill_review_queue import SkillDraftVersion, SkillReviewQueueBridge, SkillReviewQueueItem
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.tool_result import ToolResultStatus
from tiangong_agent_shell.tool_bridge import ToolExecutionMode

ROOT = Path(__file__).resolve().parents[1]


def test_l6_21_skill_queue_empty_state() -> None:
    bridge = SkillReviewQueueBridge()
    snapshot = bridge.public_dict()
    assert snapshot["schema"] == "tiangong.l6_21.skill_review_queue.v1"
    assert snapshot["status"] == "empty"


def test_l6_21_versions_skill_candidates_without_activation() -> None:
    experience = ExperienceSynthesisBridge().synthesize(manual_notes="把重复的质量门发布步骤沉淀成可复用 Skill。")
    queue = SkillReviewQueueBridge().queue_from_experience(experience_report=experience.public_dict(), notes="执行力优先")
    payload = queue.public_dict()
    assert payload["status"] == "queue_ready"
    assert payload["queue_only"] is True
    assert payload["execution_first"] is True
    assert payload["writes_skill_registry"] is False
    assert payload["activates_skill"] is False
    assert payload["draft_versions"]
    assert payload["review_queue"]
    assert all(item["activation_allowed"] is False for item in payload["draft_versions"])
    assert all(item["registers_skill"] is False for item in payload["draft_versions"])
    assert all(item["activates_skill"] is False for item in payload["review_queue"])


def test_l6_21_forbids_real_skill_activation_flags() -> None:
    try:
        SkillDraftVersion(
            draft_ref="skill_draft:l6_21_bad",
            source_candidate_ref="skill_candidate:l6_20_bad",
            source_lesson_refs=[],
            skill_name="bad",
            purpose="bad",
            trigger_hint="bad",
            activation_allowed=True,
        )
        raise AssertionError("SkillDraftVersion should reject real activation")
    except ValueError:
        pass
    try:
        SkillReviewQueueItem(
            review_ref="skill_review:l6_21_bad",
            draft_ref="skill_draft:l6_21_bad",
            source_candidate_ref="skill_candidate:l6_20_bad",
            activates_skill=True,
        )
        raise AssertionError("SkillReviewQueueItem should reject activation")
    except ValueError:
        pass


def test_l6_21_runtime_builds_skill_queue_from_notes(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    result = runtime.run_skill_queue_build(
        workspace=tmp_path,
        notes="把发布质量门失败经验转成 Skill 草案版本，不要激活。",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
    )
    assert result.results[-1].status is ToolResultStatus.OK
    snapshot = runtime.skill_queue_snapshot()
    assert snapshot["schema"] == "tiangong.l6_21.skill_review_queue.v1"
    assert snapshot["status"] == "queue_ready"
    assert snapshot["draft_versions"]
    assert snapshot["review_queue"]
    assert snapshot["queue_only"] is True
    assert snapshot["execution_first"] is True


def test_l6_21_tool_is_a2_and_registered() -> None:
    runtime = RuntimeEntry()
    names = {tool.name: tool.default_risk for tool in runtime.available_tools()}
    assert names["queue_skill_candidates"] == "A2"
    risk, reason = RiskClassifier().classify(ToolInvocation("queue_skill_candidates", {"notes": "入队"}))
    assert risk is RiskLevel.A2
    assert "不注册" in reason
    assert "不激活" in reason


def test_l6_21_plan_bridge_and_schema_allow_skill_queue() -> None:
    plan = PlanBridge().build_plan("技能候选入队 把重复流程转成审阅队列")
    assert [step.tool_name for step in plan] == ["synthesize_experience_candidates", "queue_skill_candidates"]
    built = validate_and_build_plan(
        {
            "steps": [
                {
                    "tool_name": "queue_skill_candidates",
                    "arguments": {"notes": "Skill 草案入队", "max_items": 3},
                }
            ]
        }
    )
    assert built[0].tool_name == "queue_skill_candidates"
    assert built[0].arguments["max_items"] == 3


def test_l6_21_cli_skill_queue_build_and_export(tmp_path: Path) -> None:
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
        input="/skill-queue-build 把重复发布流程沉淀成 Skill 草案版本，不自动注册\n/skill-queue\n/skill-queue-save skill_queue.json\n/exit\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "Skill 审阅队列" in proc.stdout
    exported = json.loads((tmp_path / "skill_queue.json").read_text(encoding="utf-8"))
    assert exported["schema"] == "tiangong.l6_21.skill_review_queue.v1"
    assert exported["queue_only"] is True
    assert exported["activates_skill"] is False


def test_l6_21_runtime_does_not_pollute_kernel_import_direction() -> None:
    kernel_root = ROOT / "tiangong_kernel"
    forbidden = ["skill_review_queue", "queue_skill_candidates", "SkillDraftVersion", "/skill-queue"]
    offenders: list[str] = []
    for path in kernel_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)}::{token}")
    assert offenders == []
