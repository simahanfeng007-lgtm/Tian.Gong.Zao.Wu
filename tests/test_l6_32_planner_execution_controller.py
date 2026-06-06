from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tiangong_agent_runtime.planner_execution_controller import (
    PLANNER_EXECUTION_SCHEMA,
    PlannerExecutionController,
    PlannerExecutionResumeEnvelope,
    stable_planner_execution_digest,
)
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.tool_result import ToolResultStatus
from tiangong_agent_shell.tool_bridge import ToolExecutionMode

ROOT = Path(__file__).resolve().parents[1]


def test_l6_32_empty_controller_is_shell_only() -> None:
    controller = PlannerExecutionController()
    snapshot = controller.public_dict()
    assert snapshot["schema"] == PLANNER_EXECUTION_SCHEMA
    assert snapshot["status"] == "empty"


def test_l6_32_execute_plan_records_lifecycle_replay_and_resume(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    runtime = RuntimeEntry()
    result = runtime.execute_plan(
        [
            ToolInvocation("list_dir", {"path": "."}),
            ToolInvocation("read_file", {"path": "README.md"}),
        ],
        workspace=tmp_path,
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps=4,
    )
    assert [item.status for item in result.results] == [ToolResultStatus.OK, ToolResultStatus.OK]
    report = runtime.planner_execution_snapshot()
    assert report["schema"] == PLANNER_EXECUTION_SCHEMA
    assert report["status"] == "completed"
    assert report["total_steps"] == 2
    assert report["executed_steps"] == 2
    assert report["succeeded_steps"] == 2
    assert report["failed_steps"] == 0
    assert report["uses_long_chain_runner"] is True
    assert report["uses_execution_spine"] is True
    assert report["no_parallel_runtime"] is True
    assert report["no_direct_adapter_call"] is True
    assert report["no_kernel_mutation"] is True
    assert report["resume_envelope"]["resume_mode"] == "completed"
    assert report["resume_envelope"]["can_resume"] is False
    assert report["replay_event_count"] >= 6
    assert all(record["state_history"][:2] == ["planned", "running"] for record in report["step_records"])
    assert all(record["state"] == "succeeded" for record in report["step_records"])
    assert stable_planner_execution_digest(report) == report["report_digest"]


def test_l6_32_failure_stops_chain_and_emits_resume_envelope(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    result = runtime.execute_plan(
        [
            ToolInvocation("read_file", {"path": "missing.txt"}),
            ToolInvocation("write_workspace_file", {"path": "after_failure.txt", "content": "should not run"}),
        ],
        workspace=tmp_path,
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps=5,
    )
    assert result.results[0].status is ToolResultStatus.FAILED
    assert not (tmp_path / "after_failure.txt").exists()
    report = runtime.planner_execution_snapshot()
    assert report["status"] == "failed_with_resume"
    assert report["failed_steps"] == 1
    assert report["skipped_steps"] == 1
    assert report["stopped_reason"] == "failure_budget_exhausted"
    resume = report["resume_envelope"]
    assert resume["resume_mode"] == "recover_failed_step"
    assert resume["can_resume"] is True
    assert resume["next_step_index"] == 1
    assert resume["remaining_step_count"] == 2
    assert report["step_records"][1]["state"] == "skipped"


def test_l6_32_a4_confirmation_and_a5_block_are_terminal_resume_modes(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    a4 = runtime.execute_plan(
        [ToolInvocation("write_workspace_file", {"path": str(tmp_path / "absolute.txt"), "content": "x"})],
        workspace=tmp_path,
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps=1,
    )
    assert a4.results[0].status is ToolResultStatus.CONFIRMATION_REQUIRED
    a4_report = runtime.planner_execution_snapshot()
    assert a4_report["status"] == "confirmation_required"
    assert a4_report["resume_envelope"]["resume_mode"] == "await_confirmation"
    assert a4_report["resume_envelope"]["confirmation_ticket_ids"]

    a5 = runtime.execute_plan(
        [ToolInvocation("read_file", {"path": ".env"})],
        workspace=tmp_path,
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps=1,
    )
    assert a5.results[0].status is ToolResultStatus.BLOCKED
    a5_report = runtime.planner_execution_snapshot()
    assert a5_report["status"] == "blocked"
    assert a5_report["blocked_steps"] == 1
    assert a5_report["resume_envelope"]["resume_mode"] == "blocked_replan"
    assert a5_report["resume_envelope"]["can_resume"] is False


def test_l6_32_runtime_planner_execution_task_uses_rule_or_model_plan(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    runtime = RuntimeEntry()
    result = runtime.run_planner_execution_task(
        "read README.md",
        workspace=tmp_path,
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        planner_mode="rule_only",
        max_steps=3,
    )
    assert result.intent.intent == "planner_execution"
    assert result.results[0].status is ToolResultStatus.OK
    assert result.planner_execution_report is not None
    report = runtime.planner_execution_snapshot()
    assert report["schema"] == PLANNER_EXECUTION_SCHEMA
    assert report["status"] == "completed"
    assert "L6.32 Planner 执行主链摘要" in runtime._build_planner_context_hint()


def test_l6_32_resume_envelope_rejects_execution_or_kernel_mutation() -> None:
    try:
        PlannerExecutionResumeEnvelope(
            resume_mode="bad",
            can_resume=True,
            next_step_index=1,
            direct_execution_now=True,
        )
        raise AssertionError("resume envelope should reject direct execution")
    except ValueError:
        pass
    try:
        PlannerExecutionResumeEnvelope(
            resume_mode="bad",
            can_resume=True,
            next_step_index=1,
            touches_kernel=True,
        )
        raise AssertionError("resume envelope should reject kernel mutation")
    except ValueError:
        pass


def test_l6_32_cli_planner_execute_and_export(tmp_path: Path) -> None:
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
        input="/planner-execute read README.md\n/planner-execution\n/planner-execution-save planner_execution.json\n/exit\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "L6.32 执行主链" in proc.stdout
    exported = json.loads((tmp_path / "planner_execution.json").read_text(encoding="utf-8"))
    assert exported["schema"] == PLANNER_EXECUTION_SCHEMA
    assert exported["status"] == "completed"
    assert exported["uses_long_chain_runner"] is True
    assert exported["uses_execution_spine"] is True
    assert exported["no_kernel_mutation"] is True
