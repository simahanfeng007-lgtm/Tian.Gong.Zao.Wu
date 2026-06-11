"""L6.72.45 文档追问、引用、导出与修改计划 adapters。"""

from __future__ import annotations

import json
from typing import Any

from ..document_context_store import (
    build_rewrite_plan,
    load_document_context,
    public_context_payload,
    query_document_context,
    render_context_markdown,
    render_context_text,
    safe_text,
    save_document_context,
)
from ..document_parser import parse_document
from ..host_path_normalizer import normalize_argument_path, normalization_public_data
from ..physical_commit import write_text_atomic_verified
from ..result_normalizer import truncate_text
from ..tool_invocation import ToolInvocation
from ..tool_result import ToolResult, ToolResultStatus
from ..turn_context import TurnContext
from ..workspace_guard import WorkspaceGuard, WorkspaceViolation


def _to_int(value: Any, default: int = 6, *, minimum: int = 1, maximum: int = 20) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(number, maximum))


def _load_or_parse_context(invocation: ToolInvocation, context: TurnContext) -> tuple[dict[str, Any] | None, str]:
    document_id = safe_text(invocation.arguments.get("document_id"), 100)
    raw_path = invocation.arguments.get("path") or invocation.arguments.get("source") or ""
    if raw_path:
        guard = WorkspaceGuard(context.workspace)
        normalized_path, _path_normalization = normalize_argument_path(raw_path, context.user_message)
        target = guard.resolve_for_read(normalized_path)
        parsed = parse_document(target, max_chars=int(invocation.arguments.get("max_chars") or context.policy.max_output_chars))
        ctx, _ = save_document_context(context.workspace, parsed)
        return ctx, "parsed_from_path"
    ctx = load_document_context(context.workspace, document_id=document_id)
    return ctx, "loaded_from_context" if ctx else "missing_context"


def document_query_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
    try:
        ctx, source = _load_or_parse_context(invocation, context)
        if not ctx:
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.FAILED,
                "没有可追问的文档上下文。请先用 document_parse 解析文档，或在 document_query 中传入 path。",
                error_code="document_context_missing",
            )
        query = safe_text(invocation.arguments.get("query") or context.user_message, 800)
        top_k = _to_int(invocation.arguments.get("top_k") or invocation.arguments.get("limit") or 6, 6)
        result = query_document_context(ctx, query, top_k=top_k)
        result["context_source"] = source
        ok = result.get("status") in {"ok", "partial"}
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK if ok else ToolResultStatus.FAILED,
            output_summary=truncate_text(str(result.get("answer_summary") or "文档追问完成。"), context.policy.max_output_chars),
            data=result,
            error_code="" if ok else "document_query_failed",
        )
    except WorkspaceViolation as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.BLOCKED, str(exc), error_code="workspace_violation")
    except OSError as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"文档追问读取失败：{exc}", error_code="os_error")


def document_export_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
    try:
        ctx, source = _load_or_parse_context(invocation, context)
        if not ctx:
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.FAILED,
                "没有可导出的文档上下文。请先用 document_parse 解析文档，或在 document_export 中传入 path。",
                error_code="document_context_missing",
            )
        fmt = safe_text(invocation.arguments.get("format") or invocation.arguments.get("output_format") or "md", 20).lower().lstrip(".")
        if fmt not in {"md", "markdown", "txt", "json"}:
            fmt = "md"
        document_id = safe_text(ctx.get("document_id"), 80)
        default_suffix = "json" if fmt == "json" else ("txt" if fmt == "txt" else "md")
        target_arg = invocation.arguments.get("target") or invocation.arguments.get("output_path") or f"document_exports/{document_id}_summary.{default_suffix}"
        guard = WorkspaceGuard(context.workspace)
        normalized_target_arg, path_normalization = normalize_argument_path(target_arg, context.user_message)
        target = guard.resolve_for_artifact(normalized_target_arg)

        query_result = None
        query = safe_text(invocation.arguments.get("query"), 800)
        if query:
            query_result = query_document_context(ctx, query, top_k=_to_int(invocation.arguments.get("top_k") or 8, 8))
        if fmt == "json":
            payload = public_context_payload(ctx)
            if query_result:
                payload["query_result"] = query_result
            content = json.dumps(payload, ensure_ascii=False, indent=2)
        elif fmt == "txt":
            content = render_context_text(ctx, query_result=query_result)
        else:
            content = render_context_markdown(ctx, query_result=query_result)
        commit = write_text_atomic_verified(target, content, encoding="utf-8")
        try:
            rel = target.relative_to(context.workspace).as_posix()
        except ValueError:
            rel = str(target)
        if not commit.get("physical_commit_verified"):
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.FAILED,
                "文档导出写入后物理落盘验真失败：未向用户报告导出成功。",
                error_code="physical_commit_verification_failed",
                data={"target": rel, "normalized_host_path": normalization_public_data(path_normalization), "commit": commit, "raw_bytes_hidden": True},
            )
        summary = "\n".join(
            [
                "【文档导出】",
                f"- 文档 ID：{document_id}",
                f"- 来源：{source}",
                f"- 格式：{fmt}",
                f"- 输出：{rel}",
                "- 状态：已完成物理落盘验真。",
                "- 边界：只导出安全解析片段和引用编号，不包含原始二进制、stderr 或工具 raw result。",
            ]
        )
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=truncate_text(summary, context.policy.max_output_chars),
            data={"document_id": document_id, "target": rel, "format": fmt, "raw_bytes_hidden": True, "physical_commit_verified": True, "normalized_host_path": normalization_public_data(path_normalization), "commit": commit},
            artifacts=[rel],
        )
    except WorkspaceViolation as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.BLOCKED, str(exc), error_code="workspace_violation")
    except OSError as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"文档导出失败：{exc}", error_code="os_error")


def document_rewrite_plan_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
    try:
        ctx, source = _load_or_parse_context(invocation, context)
        if not ctx:
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.FAILED,
                "没有可进入修改闭环的文档上下文。请先解析文档，或在 document_rewrite_plan 中传入 path。",
                error_code="document_context_missing",
            )
        instruction = safe_text(invocation.arguments.get("instruction") or invocation.arguments.get("query") or context.user_message, 1200)
        output_path = safe_text(invocation.arguments.get("output_path") or invocation.arguments.get("target"), 500)
        output_format = safe_text(invocation.arguments.get("output_format") or invocation.arguments.get("format"), 80)
        result = build_rewrite_plan(ctx, instruction, output_path=output_path, output_format=output_format)
        result["context_source"] = source
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=truncate_text(str(result.get("answer_summary") or "文档修改计划已生成。"), context.policy.max_output_chars),
            data=result,
        )
    except WorkspaceViolation as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.BLOCKED, str(exc), error_code="workspace_violation")
    except OSError as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"文档修改计划读取失败：{exc}", error_code="os_error")
