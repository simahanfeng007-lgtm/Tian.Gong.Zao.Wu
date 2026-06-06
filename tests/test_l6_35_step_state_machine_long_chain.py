from __future__ import annotations

from pathlib import Path

from tiangong_agent_runtime.long_chain_pressure_probe import (
    L6_35_PRESSURE_SCHEMA,
    build_pressure_plan,
    run_long_chain_pressure_probe,
)
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.runtime_tool_registry import ToolDescriptor
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.tool_result import ToolResult, ToolResultStatus
from tiangong_agent_shell.tool_bridge import ToolExecutionMode


def _prepare_workspace(tmp_path: Path) -> Path:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    return tmp_path


def test_l6_35_step_record_has_full_lifecycle_timing_and_evidence(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    result = runtime.execute_plan(
        [ToolInvocation("list_dir", {"path": "."}), ToolInvocation("read_file", {"path": "README.md"})],
        workspace=_prepare_workspace(tmp_path),
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps=4,
    )
    assert [item.status for item in result.results] == [ToolResultStatus.OK, ToolResultStatus.OK]
    report = runtime.planner_execution_snapshot()
    assert report["schema"] == "tiangong.l6_35.planner_execution_controller.v1"
    assert report["status"] == "completed"
    assert report["timeout_steps"] == 0
    for record in report["step_records"]:
        assert record["state"] == "succeeded"
        assert record["state_history"][:2] == ["planned", "running"]  # 旧 L6.32 兼容
        assert record["lifecycle_states"] == ["planned", "queued", "running", "succeeded"]
        assert record["adapter_name"] == record["tool_name"]
        assert record["started_at"] > 0
        assert record["finished_at"] >= record["started_at"]
        assert record["duration_ms"] >= 0
        assert record["evidence_refs"]
    assert {event["event_type"] for event in report["replay_events"]} >= {"planned", "queued", "running", "succeeded"}


def test_l6_35_long_chain_pressure_probe_runs_20_50_100(tmp_path: Path) -> None:
    report = run_long_chain_pressure_probe(tmp_path, step_counts=(20, 50, 100))
    payload = report.public_dict()
    assert payload["schema"] == L6_35_PRESSURE_SCHEMA
    assert payload["ok"] is True
    assert [case["step_count"] for case in payload["cases"]] == [20, 50, 100]
    for case in payload["cases"]:
        assert case["status"] == "completed"
        assert case["executed_steps"] == case["step_count"]
        assert case["succeeded_steps"] == case["step_count"]
        assert case["failed_steps"] == 0
        assert case["timeout_steps"] == 0
        assert case["progress_snapshot_count"] == case["step_count"] // 5
        assert case["replay_event_count"] >= case["step_count"] * 4
        assert case["resume_mode"] == "completed"
        assert case["can_resume"] is False


def test_l6_35_resume_does_not_rerun_succeeded_steps(tmp_path: Path) -> None:
    workspace = _prepare_workspace(tmp_path)
    runtime = RuntimeEntry()
    original_plan = [
        ToolInvocation("return_analysis", {"content": "step one"}, step_id="resume_001"),
        ToolInvocation("read_file", {"path": "missing.txt"}, step_id="resume_002"),
        ToolInvocation("return_analysis", {"content": "step three"}, step_id="resume_003"),
    ]
    first = runtime.execute_plan(original_plan, workspace=workspace, tool_mode=ToolExecutionMode.RUNTIME_GOVERNED, max_steps=5)
    assert [item.step_id for item in first.results] == ["resume_001", "resume_002"]
    first_report = runtime.planner_execution_snapshot()
    assert first_report["resume_envelope"]["can_resume"] is True
    assert first_report["resume_envelope"]["next_step_index"] == 2

    (workspace / "fixed.txt").write_text("fixed\n", encoding="utf-8")
    repaired_plan = [
        original_plan[0],
        ToolInvocation("read_file", {"path": "fixed.txt"}, step_id="resume_002"),
        original_plan[2],
    ]
    resumed = runtime.resume_plan(
        repaired_plan,
        previous_report=first_report,
        workspace=workspace,
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps=5,
    )
    assert [item.step_id for item in resumed.results] == ["resume_002", "resume_003"]
    resumed_report = runtime.planner_execution_snapshot()
    assert resumed_report["status"] == "completed"
    assert resumed_report["resumed_from_report_digest"] == first_report["report_digest"]
    assert resumed_report["original_total_steps"] == 3
    assert resumed_report["resumed_from_next_step_index"] == 2
    assert resumed_report["executed_steps"] == 2


def test_l6_35_timeout_is_separate_from_failure_budget(tmp_path: Path) -> None:
    workspace = _prepare_workspace(tmp_path)
    runtime = RuntimeEntry()

    def timeout_adapter(invocation: ToolInvocation, context) -> ToolResult:  # noqa: ANN001
        return ToolResult(
            invocation.step_id,
            invocation.tool_name,
            ToolResultStatus.TIMEOUT,
            "adapter timed out",
            error_code="timeout",
        )

    runtime.registry.register(ToolDescriptor("diagnose_timeout", "测试用超时诊断工具。", "A1"), timeout_adapter)
    result = runtime.execute_plan(
        [
            ToolInvocation("diagnose_timeout", {"path": "."}, step_id="timeout_001"),
            ToolInvocation("return_analysis", {"content": "should not run"}, step_id="timeout_002"),
        ],
        workspace=workspace,
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps=5,
    )
    assert result.results[0].status is ToolResultStatus.TIMEOUT
    assert result.chain_summary is not None
    assert result.chain_summary.failure_count == 0
    assert result.chain_summary.stopped_reason == "timeout"
    report = runtime.planner_execution_snapshot()
    assert report["status"] == "timeout_with_resume"
    assert report["timeout_steps"] == 1
    assert report["failed_steps"] == 0
    assert report["skipped_steps"] == 1
    assert report["resume_envelope"]["resume_mode"] == "recover_timeout_step"
    assert report["resume_envelope"]["can_resume"] is True


def test_l6_35_blocked_and_confirmation_do_not_consume_failure_budget(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    blocked = runtime.execute_plan(
        [ToolInvocation("read_file", {"path": ".env"}), ToolInvocation("return_analysis", {"content": "after"})],
        workspace=tmp_path,
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps=4,
    )
    assert blocked.chain_summary is not None
    assert blocked.chain_summary.failure_count == 0
    blocked_report = runtime.planner_execution_snapshot()
    assert blocked_report["blocked_steps"] == 1
    assert blocked_report["failed_steps"] == 0
    assert blocked_report["skipped_steps"] == 1

    confirmed = runtime.execute_plan(
        [ToolInvocation("write_workspace_file", {"path": str(tmp_path / "absolute.txt"), "content": "x"})],
        workspace=tmp_path,
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps=1,
    )
    assert confirmed.chain_summary is not None
    assert confirmed.chain_summary.failure_count == 0
    confirm_report = runtime.planner_execution_snapshot()
    assert confirm_report["confirmation_required_steps"] == 1
    assert confirm_report["failed_steps"] == 0


def test_l6_35_replay_events_are_ordered_and_digest_is_stable(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    runtime.execute_plan(build_pressure_plan(20), workspace=_prepare_workspace(tmp_path), tool_mode=ToolExecutionMode.RUNTIME_GOVERNED, max_steps=25)
    report = runtime.planner_execution_snapshot()
    event_indexes = [event["event_index"] for event in report["replay_events"]]
    assert event_indexes == sorted(event_indexes)
    assert len(event_indexes) == len(set(event_indexes))
    assert report["report_digest"]
    assert report["progress_snapshot_count"] == 4
    assert all(snapshot["completed_steps"] % 5 == 0 for snapshot in report["progress_snapshots"])


def test_l6_35_pressure_report_exports_json_and_markdown(tmp_path: Path) -> None:
    report = run_long_chain_pressure_probe(tmp_path, step_counts=(20,))
    json_path = report.export_json(tmp_path / "pressure.json")
    assert json_path.exists()
    text = report.markdown_report()
    assert "L6.35 长链压力回放报告" in text
    assert "pressure_20" in text
