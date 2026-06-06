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
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.tool_production_request import (
    SandboxValidationPlan,
    ToolProductionQueueItem,
    ToolProductionRequest,
    ToolProductionRequestBridge,
)
from tiangong_agent_runtime.tool_result import ToolResultStatus
from tiangong_agent_shell.tool_bridge import ToolExecutionMode

ROOT = Path(__file__).resolve().parents[1]


def test_l6_22_tool_request_empty_state() -> None:
    bridge = ToolProductionRequestBridge()
    snapshot = bridge.public_dict()
    assert snapshot["schema"] == "tiangong.l6_22.tool_production_request.v1"
    assert snapshot["status"] == "empty"


def test_l6_22_turns_tool_gaps_into_requests_without_production() -> None:
    experience = ExperienceSynthesisBridge().synthesize(manual_notes="missing_tests pytest_missing test gap should become tool gap candidate")
    report = ToolProductionRequestBridge().queue_from_experience(experience_report=experience.public_dict(), notes="执行力优先")
    payload = report.public_dict()
    assert payload["status"] == "request_ready"
    assert payload["request_only"] is True
    assert payload["execution_first"] is True
    assert payload["sandbox_preflight_only"] is True
    assert payload["production_requests"]
    assert payload["sandbox_validation_plans"]
    assert payload["review_queue"]
    assert all(item["produces_tool"] is False for item in payload["production_requests"])
    assert all(item["writes_tool_code"] is False for item in payload["production_requests"])
    assert all(item["registers_tool"] is False for item in payload["production_requests"])
    assert all(item["releases_tool_handle"] is False for item in payload["production_requests"])
    assert all(item["executes_sandbox"] is False for item in payload["sandbox_validation_plans"])


def test_l6_22_forbids_real_tool_production_flags() -> None:
    try:
        ToolProductionRequest(
            request_ref="tool_request:l6_22_bad",
            source_candidate_ref="tool_gap:l6_20_bad",
            source_lesson_refs=[],
            tool_name_hint="bad",
            capability_need="bad",
            governance_requirement="bad",
            produces_tool=True,
        )
        raise AssertionError("ToolProductionRequest should reject real tool production")
    except ValueError:
        pass
    try:
        SandboxValidationPlan(
            validation_ref="sandbox_validation:l6_22_bad",
            request_ref="tool_request:l6_22_bad",
            executes_sandbox=True,
        )
        raise AssertionError("SandboxValidationPlan should reject execution in L6.22")
    except ValueError:
        pass
    try:
        ToolProductionQueueItem(
            queue_ref="tool_request_queue:l6_22_bad",
            request_ref="tool_request:l6_22_bad",
            validation_ref="sandbox_validation:l6_22_bad",
            source_candidate_ref="tool_gap:l6_20_bad",
            releases_tool_handle=True,
        )
        raise AssertionError("ToolProductionQueueItem should reject tool handle release")
    except ValueError:
        pass


def test_l6_22_runtime_builds_tool_request_queue_from_notes(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    result = runtime.run_tool_request_build(
        workspace=tmp_path,
        notes="missing_tests pytest_missing test 缺工具，生成 Tool 生产请求，但不要生产工具。",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
    )
    assert result.results[-1].status is ToolResultStatus.OK
    snapshot = runtime.tool_request_snapshot()
    assert snapshot["schema"] == "tiangong.l6_22.tool_production_request.v1"
    assert snapshot["status"] == "request_ready"
    assert snapshot["production_requests"]
    assert snapshot["sandbox_validation_plans"]
    assert snapshot["review_queue"]
    assert snapshot["produces_tool"] is False
    assert snapshot["registers_tool"] is False
    assert snapshot["releases_tool_handle"] is False


def test_l6_22_tool_is_a2_and_registered() -> None:
    runtime = RuntimeEntry()
    names = {tool.name: tool.default_risk for tool in runtime.available_tools()}
    assert names["queue_tool_production_requests"] == "A2"
    risk, reason = RiskClassifier().classify(ToolInvocation("queue_tool_production_requests", {"notes": "入队"}))
    assert risk is RiskLevel.A2
    assert "不生产" in reason
    assert "不注册" in reason
    assert "不释放" in reason


def test_l6_22_plan_bridge_and_schema_allow_tool_request_queue() -> None:
    plan = PlanBridge().build_plan("工具生产请求 missing_tests pytest_missing test 进入沙箱验证前置")
    assert [step.tool_name for step in plan] == ["synthesize_experience_candidates", "queue_tool_production_requests"]
    built = validate_and_build_plan(
        {
            "steps": [
                {
                    "tool_name": "queue_tool_production_requests",
                    "arguments": {"notes": "Tool 缺口入队", "max_items": 3},
                }
            ]
        }
    )
    assert built[0].tool_name == "queue_tool_production_requests"
    assert built[0].arguments["max_items"] == 3


def test_l6_22_cli_tool_request_build_and_export(tmp_path: Path) -> None:
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
        input="/tool-request-build missing_tests pytest_missing test 缺工具，生成生产请求，不自动注册\n/tool-request\n/tool-request-save tool_requests.json\n/exit\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "Tool 生产请求" in proc.stdout
    exported = json.loads((tmp_path / "tool_requests.json").read_text(encoding="utf-8"))
    assert exported["schema"] == "tiangong.l6_22.tool_production_request.v1"
    assert exported["request_only"] is True
    assert exported["produces_tool"] is False
    assert exported["registers_tool"] is False


def test_l6_22_runtime_does_not_pollute_kernel_import_direction() -> None:
    kernel_root = ROOT / "tiangong_kernel"
    forbidden = ["tool_production_request", "queue_tool_production_requests", "/tool-request"]
    offenders: list[str] = []
    for path in kernel_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)}::{token}")
    assert offenders == []
