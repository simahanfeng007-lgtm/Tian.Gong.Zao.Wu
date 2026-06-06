from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tiangong_agent_runtime.experience_synthesis import ExperienceSynthesisBridge, SkillCandidate, ToolGapCandidate
from tiangong_agent_runtime.plan_bridge import PlanBridge
from tiangong_agent_runtime.plan_schema import validate_and_build_plan
from tiangong_agent_runtime.risk_classifier import RiskClassifier
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.tool_result import ToolResultStatus
from tiangong_agent_runtime.execution_policy import RiskLevel
from tiangong_agent_shell.tool_bridge import ToolExecutionMode

ROOT = Path(__file__).resolve().parents[1]


def _seed_project(root: Path, *, with_tests: bool = False) -> None:
    (root / "README.md").write_text("# Demo\n", encoding="utf-8")
    (root / "demo.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    if with_tests:
        (root / "test_demo.py").write_text("from demo import add\n\ndef test_add():\n    assert add(1, 2) == 3\n", encoding="utf-8")


def test_l6_20_bridge_empty_state_is_candidate_only() -> None:
    bridge = ExperienceSynthesisBridge()
    snapshot = bridge.public_dict()
    assert snapshot["schema"] == "tiangong.l6_20.experience_synthesis.v1"
    assert snapshot["status"] == "empty"


def test_l6_20_manual_reflection_generates_skill_candidate_without_side_effects() -> None:
    bridge = ExperienceSynthesisBridge()
    report = bridge.synthesize(manual_notes="质量门 warn 时必须先披露风险，再进入发布链。")
    payload = report.public_dict()
    assert payload["status"] == "candidate_ready"
    assert payload["candidate_only"] is True
    assert payload["writes_skill_registry"] is False
    assert payload["produces_tool"] is False
    assert payload["applies_change"] is False
    assert payload["skill_candidates"]
    assert payload["governance_transfers"]


def test_l6_20_forbids_real_skill_or_tool_effect_flags() -> None:
    try:
        SkillCandidate(
            candidate_ref="skill_candidate:l6_20_bad",
            source_lesson_refs=["lesson:l6_20_bad"],
            skill_name="bad",
            purpose="bad",
            trigger_hint="bad",
            registers_skill=True,
        )
        raise AssertionError("SkillCandidate should reject real registration")
    except ValueError:
        pass
    try:
        ToolGapCandidate(
            candidate_ref="tool_gap:l6_20_bad",
            source_lesson_refs=["lesson:l6_20_bad"],
            tool_gap_name="bad",
            capability_need="bad",
            governance_requirement="bad",
            produces_tool=True,
        )
        raise AssertionError("ToolGapCandidate should reject real tool production")
    except ValueError:
        pass


def test_l6_20_runtime_synthesizes_from_quality_gate_and_diagnosis(tmp_path: Path) -> None:
    _seed_project(tmp_path, with_tests=False)
    runtime = RuntimeEntry()
    runtime.run_quality_gate(
        workspace=tmp_path,
        path=".",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        require_pytest=True,
        package_on_pass=False,
    )
    result = runtime.run_experience_synthesis(
        workspace=tmp_path,
        notes="把 missing_tests 经验转成候选，但不要自动写测试。",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
    )
    assert result.results[-1].status is ToolResultStatus.OK
    snapshot = runtime.experience_snapshot()
    assert snapshot["schema"] == "tiangong.l6_20.experience_synthesis.v1"
    assert snapshot["status"] == "candidate_ready"
    assert snapshot["skill_candidates"]
    assert snapshot["tool_gap_candidates"]
    assert all(item["produces_tool"] is False for item in snapshot["tool_gap_candidates"])
    assert all(item["registers_skill"] is False for item in snapshot["skill_candidates"])


def test_l6_20_experience_tool_is_a2_and_registered() -> None:
    runtime = RuntimeEntry()
    names = {tool.name: tool.default_risk for tool in runtime.available_tools()}
    assert names["synthesize_experience_candidates"] == "A2"
    risk, reason = RiskClassifier().classify(ToolInvocation("synthesize_experience_candidates", {"notes": "复盘"}))
    assert risk is RiskLevel.A2
    assert "不注册" in reason


def test_l6_20_plan_bridge_and_plan_schema_allow_candidate_tool() -> None:
    plan = PlanBridge().build_plan("总结经验 质量门失败后先修复再发布")
    assert len(plan) == 1
    assert plan[0].tool_name == "synthesize_experience_candidates"
    built = validate_and_build_plan(
        {
            "steps": [
                {
                    "tool_name": "synthesize_experience_candidates",
                    "arguments": {"notes": "复盘候选", "max_candidates": 5},
                }
            ]
        }
    )
    assert built[0].arguments["max_candidates"] == 5


def test_l6_20_redacts_secret_like_manual_notes() -> None:
    report = ExperienceSynthesisBridge().synthesize(manual_notes="api_key=sk-test-secret token=abc123 应该脱敏")
    text = json.dumps(report.public_dict(), ensure_ascii=False)
    assert "sk-test-secret" not in text
    assert "abc123" not in text
    assert "<redacted>" in text


def test_l6_20_cli_reflect_experience_and_export(tmp_path: Path) -> None:
    _seed_project(tmp_path, with_tests=True)
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
        input="/reflect 质量门 warn 时沉淀为 Skill 候选，不要自动注册\n/experience\n/experience-save experience.json\n/exit\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "经验沉淀" in proc.stdout
    assert "经验沉淀候选报告已导出" in proc.stdout
    exported = json.loads((tmp_path / "experience.json").read_text(encoding="utf-8"))
    assert exported["schema"] == "tiangong.l6_20.experience_synthesis.v1"
    assert exported["candidate_only"] is True


def test_l6_20_runtime_does_not_pollute_kernel_import_direction() -> None:
    kernel_root = ROOT / "tiangong_kernel"
    forbidden = ["experience_synthesis", "synthesize_experience_candidates", "SkillCandidate", "ToolGapCandidate", "/reflect"]
    offenders: list[str] = []
    for path in kernel_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)}::{token}")
    assert offenders == []
