"""L6.72.45 document_parse Runtime adapter：解析后建立可追问上下文。"""

from __future__ import annotations

from ..document_context_store import save_document_context
from ..host_path_normalizer import normalize_argument_path, normalization_public_data
from ..document_parser import parse_document
from ..result_normalizer import truncate_text
from ..tool_invocation import ToolInvocation
from ..tool_result import ToolResult, ToolResultStatus
from ..turn_context import TurnContext
from ..workspace_guard import WorkspaceGuard, WorkspaceViolation


def document_parse_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
    guard = WorkspaceGuard(context.workspace)
    try:
        raw_path = invocation.arguments.get("path") or ""
        normalized_path, path_normalization = normalize_argument_path(raw_path, context.user_message)
        target = guard.resolve_for_read(normalized_path)
        parsed = parse_document(target, max_chars=int(invocation.arguments.get("max_chars") or context.policy.max_output_chars))
        _, parsed = save_document_context(context.workspace, parsed)
        status = ToolResultStatus.OK if parsed.get("status") in {"ok", "partial"} else ToolResultStatus.FAILED
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=status,
            output_summary=truncate_text(str(parsed.get("human_readable_summary") or parsed.get("summary") or "文档解析完成。"), context.policy.max_output_chars),
            data={**{k: v for k, v in parsed.items() if k not in {"content_preview"}}, "normalized_host_path": normalization_public_data(path_normalization)},
            error_code="" if status is ToolResultStatus.OK else str(parsed.get("diagnostics") or "document_parse_failed"),
        )
    except WorkspaceViolation as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.BLOCKED, str(exc), error_code="workspace_violation")
    except OSError as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"文档解析读取失败：{exc}", error_code="os_error")
