from __future__ import annotations

from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry


def test_long_chain_executes_multi_step_with_checkpoints(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    result = runtime.run_text(
        "write a.txt :: hello && read a.txt && zip . dist/a.zip",
        workspace=tmp_path,
        tool_mode="runtime_governed",
    )
    assert result.projection.status == "ok"
    assert result.chain_summary is not None
    assert result.chain_summary.total_steps == 3
    assert result.chain_summary.executed_steps == 3
    assert result.chain_summary.stopped_reason == "completed"
    assert [cp.tool_name for cp in result.chain_summary.checkpoints] == [
        "write_workspace_file",
        "read_file",
        "create_zip_package",
    ]
    assert (tmp_path / "a.txt").read_text(encoding="utf-8") == "hello"
    assert (tmp_path / "dist" / "a.zip").exists()


def test_long_chain_stops_on_failed_step_before_later_write(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    result = runtime.run_text(
        "read missing.txt && write should_not_exist.txt :: x",
        workspace=tmp_path,
        tool_mode="runtime_governed",
    )
    assert result.chain_summary is not None
    assert result.chain_summary.executed_steps == 1
    assert result.chain_summary.stopped_reason == "failure_budget_exhausted"
    assert not (tmp_path / "should_not_exist.txt").exists()


def test_long_chain_stops_on_confirmation_required(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    absolute_target = tmp_path / "abs.txt"
    result = runtime.run_text(
        f"write {absolute_target} :: x && write after.txt :: y",
        workspace=tmp_path,
        tool_mode="runtime_governed",
    )
    assert result.chain_summary is not None
    assert result.chain_summary.executed_steps == 1
    assert result.chain_summary.stopped_reason == "confirmation_required"
    assert result.results[0].status.value == "confirmation_required"
    assert not absolute_target.exists()
    assert not (tmp_path / "after.txt").exists()
