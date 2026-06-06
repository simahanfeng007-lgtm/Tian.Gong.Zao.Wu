"""错误映射。"""

from __future__ import annotations

from .tool_result import ToolResult, ToolResultStatus


def failed_result(step_id: str, tool_name: str, message: str, *, code: str = "runtime_error") -> ToolResult:
    return ToolResult(
        step_id=step_id,
        tool_name=tool_name,
        status=ToolResultStatus.FAILED,
        output_summary=message,
        error_code=code,
    )
