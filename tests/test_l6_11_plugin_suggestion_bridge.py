from __future__ import annotations

from pathlib import Path

from tiangong_agent_runtime.plugin_suggestion_bridge import PluginSuggestionBridge
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.suggestions import PlanSuggestion, QualityGateSuggestion


def test_plugin_plan_suggestion_converts_to_invocations_without_direct_execution() -> None:
    suggestion = PlanSuggestion(
        source_plugin="product_delivery",
        summary="生成交付说明",
        steps=[{"tool_name": "write_workspace_file", "arguments": {"path": "report.txt", "content": "ok"}}],
        confidence=0.9,
    )
    result = PluginSuggestionBridge().to_plan([suggestion])
    assert result.accepted_count == 1
    assert result.plan[0].tool_name == "write_workspace_file"
    assert result.rejected == []


def test_plugin_direct_execution_request_is_rejected() -> None:
    suggestion = PlanSuggestion(
        source_plugin="unsafe_plugin",
        summary="试图直通执行",
        steps=[{"tool_name": "write_workspace_file", "arguments": {"path": "x.txt", "content": "x"}}],
        direct_execution_requested=True,
    )
    result = PluginSuggestionBridge().to_plan([suggestion])
    assert result.plan == []
    assert "请求直接执行" in result.rejected[0]


def test_plugin_unknown_tool_is_rejected() -> None:
    suggestion = PlanSuggestion(
        source_plugin="adaptive_collaboration",
        summary="未知工具建议",
        steps=[{"tool_name": "terminal_shell", "arguments": {"command": "echo x"}}],
    )
    result = PluginSuggestionBridge().to_plan([suggestion])
    assert result.plan == []
    assert "未允许的建议工具 terminal_shell" in result.rejected[0]


def test_quality_gate_suggestion_generates_quality_check_plan() -> None:
    suggestion = QualityGateSuggestion(
        source_plugin="final_closure",
        summary="要求 compileall",
        required_checks=["compileall"],
    )
    result = PluginSuggestionBridge().to_plan([suggestion])
    assert result.accepted_count == 1
    assert result.plan[0].tool_name == "run_python_quality_check"
    assert result.plan[0].arguments["command"] == "compileall"


def test_runtime_executes_plugin_suggestion_through_governed_spine(tmp_path: Path) -> None:
    suggestion = PlanSuggestion(
        source_plugin="product_delivery",
        summary="写入受控报告",
        steps=[{"tool_name": "write_workspace_file", "arguments": {"path": "report.txt", "content": "done"}}],
    )
    result = RuntimeEntry().execute_suggestions([suggestion], workspace=tmp_path, tool_mode="runtime_governed")
    assert result.projection.status == "ok"
    assert result.suggestion_bridge is not None
    assert result.suggestion_bridge.accepted_count == 1
    assert (tmp_path / "report.txt").read_text(encoding="utf-8") == "done"
    assert result.audit_events[0]["tool_name"] == "write_workspace_file"
