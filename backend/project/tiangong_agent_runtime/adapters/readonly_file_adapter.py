"""只读文件适配器。"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Tuple

from ..document_context_store import save_document_context
from ..host_path_normalizer import normalize_argument_path, normalization_public_data
from ..document_parser import parse_document, should_route_to_document_parse
from ..result_normalizer import truncate_text
from ..tool_invocation import ToolInvocation
from ..tool_result import ToolResult, ToolResultStatus
from ..turn_context import TurnContext
from ..workspace_guard import WorkspaceGuard, WorkspaceViolation




_TEXT_ENCODINGS = ("utf-8-sig", "utf-8", "gb18030", "cp936", "utf-16", "utf-16-le", "utf-16-be", "big5")
_BINARY_EXTENSIONS = {
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".zip", ".rar", ".7z", ".tar", ".gz", ".exe", ".dll", ".so", ".bin", ".dat", ".sqlite", ".db",
}


def _is_probably_binary(raw: bytes, suffix: str = "") -> bool:
    if not raw:
        return False
    if suffix.lower() in _BINARY_EXTENSIONS:
        return True
    sample = raw[:4096]
    if b"\x00" in sample:
        # UTF-16 text often contains NULs; let BOM-aware decoding handle it.
        if sample.startswith((b"\xff\xfe", b"\xfe\xff")):
            return False
        return True
    control = sum(1 for b in sample if b < 9 or (13 < b < 32))
    return control / max(1, len(sample)) > 0.08


def _decoded_text_score(value: str) -> float:
    if not value:
        return 1000.0
    replacement = value.count("\ufffd")
    controls = sum(1 for ch in value if ord(ch) < 32 and ch not in "\n\r\t")
    printable = sum(1 for ch in value if ch.isprintable() or ch in "\n\r\t")
    weird = replacement * 25 + controls * 10 + max(0, len(value) - printable) * 3
    return weird / max(1, len(value))


def _decode_text_bytes(raw: bytes) -> Tuple[str, str, bool]:
    best_text = ""
    best_enc = ""
    best_score = 1000.0
    for enc in _TEXT_ENCODINGS:
        try:
            candidate = raw.decode(enc)
        except UnicodeDecodeError:
            continue
        score = _decoded_text_score(candidate)
        if score < best_score:
            best_text, best_enc, best_score = candidate, enc, score
            if score == 0:
                break
    if not best_text:
        best_text = raw.decode("utf-8", errors="replace")
        best_enc = "utf-8-replace"
        best_score = _decoded_text_score(best_text)
    garbled = best_score > 0.02 or best_text.count("\ufffd") >= 3
    return best_text.replace("\x00", "").replace("\r\n", "\n"), best_enc, garbled


def _safe_file_preview(text: str, max_chars: int) -> str:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line:
            lines.append("")
            continue
        # Hide terminal escape/control sequences from chat/tool summaries.
        clean = "".join(ch for ch in line if ch.isprintable() or ch in "\t")
        lines.append(clean)
    preview = "\n".join(lines).strip()
    return truncate_text(preview, max_chars)


def list_dir_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
    guard = WorkspaceGuard(context.workspace)
    try:
        raw_path = invocation.arguments.get("path") or "."
        normalized_path, path_normalization = normalize_argument_path(raw_path, context.user_message)
        target = guard.resolve_for_read(normalized_path)
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
            data={"entries": rows, "path": str(target), "normalized_host_path": normalization_public_data(path_normalization)},
        )
    except WorkspaceViolation as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.BLOCKED, str(exc), error_code="workspace_violation")
    except OSError as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"目录读取失败：{exc}", error_code="os_error")


def file_sha256_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
    guard = WorkspaceGuard(context.workspace)
    try:
        raw_path = invocation.arguments.get("path") or ""
        normalized_path, path_normalization = normalize_argument_path(raw_path, context.user_message)
        target = guard.resolve_for_read(normalized_path)
        if not target.exists():
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, "file not found", error_code="path_not_found")
        if not target.is_file():
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, "target is not a file", error_code="not_file")
        digest = hashlib.sha256()
        size = 0
        with target.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
                size += len(chunk)
        rel = target.relative_to(context.workspace).as_posix()
        sha256 = digest.hexdigest()
        summary = f"sha256\t{rel}\t{sha256}\nbytes\t{size}"
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=truncate_text(summary, context.policy.max_output_chars),
            data={
                "path": rel,
                "sha256": sha256,
                "bytes": size,
                "normalized_host_path": normalization_public_data(path_normalization),
            },
        )
    except WorkspaceViolation as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.BLOCKED, str(exc), error_code="workspace_violation")
    except OSError as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"file sha256 failed: {exc}", error_code="os_error")


def read_file_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
    guard = WorkspaceGuard(context.workspace)
    try:
        raw_path = invocation.arguments.get("path") or ""
        normalized_path, path_normalization = normalize_argument_path(raw_path, context.user_message)
        target = guard.resolve_for_read(normalized_path)
        if not target.exists():
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, "文件不存在。", error_code="path_not_found")
        if not target.is_file():
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, "目标不是文件。", error_code="not_file")
        max_bytes = int(invocation.arguments.get("max_bytes") or 256_000)
        rel = target.relative_to(context.workspace).as_posix()
        suffix = target.suffix.lower()
        if should_route_to_document_parse(target):
            parsed = parse_document(target, max_chars=context.policy.max_output_chars)
            _, parsed = save_document_context(context.workspace, parsed)
            summary = str(parsed.get("human_readable_summary") or parsed.get("summary") or "文档解析完成。")
            return ToolResult(
                step_id=invocation.step_id,
                tool_name=invocation.tool_name,
                status=ToolResultStatus.OK if parsed.get("status") in {"ok", "partial"} else ToolResultStatus.FAILED,
                output_summary=truncate_text(summary, context.policy.max_output_chars),
                data={
                    "path": rel,
                    "parser_tool": "document_parse",
                    "document_parse": {k: v for k, v in parsed.items() if k not in {"content_preview"}},
                    "raw_bytes_hidden": True,
                    "suffix": suffix,
                    "normalized_host_path": normalization_public_data(path_normalization),
                },
                error_code="" if parsed.get("status") in {"ok", "partial"} else "document_parse_failed",
            )
        raw = target.read_bytes()[:max_bytes]
        if _is_probably_binary(raw, suffix):
            summary = (
                f"文件已读取元信息，但内容疑似二进制/富文本，read_file 不在主会话展示原始字节。\n"
                f"路径：{rel}\n"
                f"读取字节：{len(raw)}\n"
                "建议：如需解析正文，请改用 document_parse 文档解析能力；如需代码编辑，请指定普通文本源码文件。"
            )
            return ToolResult(
                step_id=invocation.step_id,
                tool_name=invocation.tool_name,
                status=ToolResultStatus.OK,
                output_summary=truncate_text(summary, context.policy.max_output_chars),
                data={"path": rel, "bytes_read": len(raw), "binary_or_rich_text": True, "suffix": suffix, "raw_bytes_hidden": True, "normalized_host_path": normalization_public_data(path_normalization)},
            )
        text, encoding, garbled = _decode_text_bytes(raw)
        if garbled:
            summary = (
                f"文件已读取，但文本编码不可可靠识别，原始内容已从主会话隐藏，避免乱码污染。\n"
                f"路径：{rel}\n"
                f"读取字节：{len(raw)}\n"
                f"尝试编码：{encoding}\n"
                "建议：确认文件编码，或转为 UTF-8 / GB18030 文本后重试。"
            )
            return ToolResult(
                step_id=invocation.step_id,
                tool_name=invocation.tool_name,
                status=ToolResultStatus.OK,
                output_summary=truncate_text(summary, context.policy.max_output_chars),
                data={"path": rel, "bytes_read": len(raw), "encoding": encoding, "encoding_uncertain": True, "normalized_host_path": normalization_public_data(path_normalization)},
            )
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=_safe_file_preview(text, context.policy.max_output_chars),
            data={"path": rel, "bytes_read": len(raw), "encoding": encoding, "normalized_host_path": normalization_public_data(path_normalization)},
        )
    except WorkspaceViolation as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.BLOCKED, str(exc), error_code="workspace_violation")
    except OSError as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"文件读取失败：{exc}", error_code="os_error")
