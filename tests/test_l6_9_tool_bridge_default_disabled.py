from __future__ import annotations

from tiangong_agent_shell.tool_bridge import ToolBridge, ToolExecutionMode


def test_tool_bridge_defaults_to_disabled() -> None:
    bridge = ToolBridge()
    result = bridge.execute("duqu_wenjian", {"path": "x"})
    assert bridge.mode is ToolExecutionMode.DISABLED
    assert result.allowed is False


def test_dry_run_does_not_allow_real_execution() -> None:
    bridge = ToolBridge("dry_run")
    result = bridge.execute("zhixing_mingling", {"cmd": "rm -rf /"})
    assert result.allowed is False
    assert result.mode is ToolExecutionMode.DRY_RUN
    assert result.payload == {"tool_name": "zhixing_mingling", "arguments": {"cmd": "rm -rf /"}}
