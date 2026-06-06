"""工作区写入适配器。"""

from __future__ import annotations

from time import time

from ..tool_invocation import ToolInvocation
from ..tool_result import ToolResult, ToolResultStatus
from ..turn_context import TurnContext
from ..workspace_guard import WorkspaceGuard, WorkspaceViolation


def write_workspace_file_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
    guard = WorkspaceGuard(context.workspace)
    try:
        target = guard.resolve_for_write(invocation.arguments.get("path") or "")
        content = str(invocation.arguments.get("content") or "")
        encoding = str(invocation.arguments.get("encoding") or "utf-8")
        target.parent.mkdir(parents=True, exist_ok=True)
        artifacts: list[str] = []
        if target.exists():
            backup = target.with_suffix(target.suffix + f".bak_{int(time())}")
            backup.write_bytes(target.read_bytes())
            artifacts.append(str(backup.relative_to(context.workspace)))
        target.write_text(content, encoding=encoding)
        artifacts.append(str(target.relative_to(context.workspace)))
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=f"已写入工作区文件：{target.relative_to(context.workspace).as_posix()}，字符数：{len(content)}。",
            artifacts=artifacts,
            data={"path": str(target.relative_to(context.workspace)), "chars": len(content)},
        )
    except WorkspaceViolation as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.BLOCKED, str(exc), error_code="workspace_violation")
    except OSError as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"文件写入失败：{exc}", error_code="os_error")
