"""只读文件适配器。"""

from __future__ import annotations

from pathlib import Path

from ..result_normalizer import truncate_text
from ..tool_invocation import ToolInvocation
from ..tool_result import ToolResult, ToolResultStatus
from ..turn_context import TurnContext
from ..workspace_guard import WorkspaceGuard, WorkspaceViolation


def list_dir_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
    guard = WorkspaceGuard(context.workspace)
    try:
        target = guard.resolve_for_read(invocation.arguments.get("path") or ".")
        if not target.exists():
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, "目录不存在。", error_code="path_not_found")
        if not target.is_dir():
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, "目标不是目录。", error_code="not_directory")
        rows = []
        for child in sorted(target.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())):
            kind = "dir" if child.is_dir() else "file"
            rel = child.relative_to(context.workspace)
            rows.append(f"{kind}\t{rel.as_posix()}")
        summary = "\n".join(rows) if rows else "<空目录>"
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=truncate_text(summary, context.policy.max_output_chars),
            data={"entries": rows, "path": str(target)},
        )
    except WorkspaceViolation as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.BLOCKED, str(exc), error_code="workspace_violation")
    except OSError as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"目录读取失败：{exc}", error_code="os_error")


def read_file_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
    guard = WorkspaceGuard(context.workspace)
    try:
        target = guard.resolve_for_read(invocation.arguments.get("path") or "")
        if not target.exists():
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, "文件不存在。", error_code="path_not_found")
        if not target.is_file():
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, "目标不是文件。", error_code="not_file")
        max_bytes = int(invocation.arguments.get("max_bytes") or 256_000)
        raw = target.read_bytes()[:max_bytes]
        text = raw.decode("utf-8", errors="replace")
        rel = target.relative_to(context.workspace).as_posix()
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=truncate_text(text, context.policy.max_output_chars),
            data={"path": rel, "bytes_read": len(raw)},
        )
    except WorkspaceViolation as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.BLOCKED, str(exc), error_code="workspace_violation")
    except OSError as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"文件读取失败：{exc}", error_code="os_error")
