"""工作区写入适配器。"""

from __future__ import annotations

from time import time
from pathlib import Path

from ..host_path_normalizer import normalize_argument_path, normalization_public_data
from ..physical_commit import write_text_atomic_verified
from ..tool_invocation import ToolInvocation
from ..tool_result import ToolResult, ToolResultStatus
from ..turn_context import TurnContext
from ..workspace_guard import WorkspaceGuard, WorkspaceViolation

_WINDOWS_PROTECTED_ROOTS = {
    "windows",
    "program files",
    "program files (x86)",
    "programdata",
    "system volume information",
    "recovery",
    "$recycle.bin",
}


def _looks_like_windows_protected_target(target: Path, workspace: Path) -> bool:
    try:
        rel_parts = [part.lower() for part in target.resolve().relative_to(workspace.resolve()).parts]
    except Exception:
        rel_parts = [part.lower() for part in target.parts]
    if not rel_parts:
        return False
    if rel_parts[0] in _WINDOWS_PROTECTED_ROOTS:
        return True
    return "system32" in rel_parts or "syswow64" in rel_parts


def write_workspace_file_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
    guard = WorkspaceGuard(context.workspace)
    try:
        raw_path = invocation.arguments.get("path") or ""
        normalized_path, path_normalization = normalize_argument_path(raw_path, context.user_message)
        target = guard.resolve_for_write(normalized_path)
        if _looks_like_windows_protected_target(target, context.workspace):
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.BLOCKED,
                "Windows 管理员权限目录写入需要显式审批/提权；已拒绝直接写入。",
                error_code="windows_permission_required",
                data={"path": str(target), "requires_administrator": True},
            )
        content = str(invocation.arguments.get("content") or "")
        encoding = str(invocation.arguments.get("encoding") or "utf-8")
        target.parent.mkdir(parents=True, exist_ok=True)
        artifacts: list[str] = []
        if target.exists():
            backup = target.with_suffix(target.suffix + f".bak_{int(time())}")
            backup.write_bytes(target.read_bytes())
            artifacts.append(str(backup.relative_to(context.workspace)))
        commit = write_text_atomic_verified(target, content, encoding=encoding)
        if not commit.get("physical_commit_verified"):
            return ToolResult(
                step_id=invocation.step_id,
                tool_name=invocation.tool_name,
                status=ToolResultStatus.FAILED,
                output_summary="文件写入后物理落盘验真失败：目标文件未能被 read-after-write 确认。未再向用户报告写入成功。",
                error_code="physical_commit_verification_failed",
                data={
                    "path": str(target.relative_to(context.workspace)),
                    "normalized_host_path": normalization_public_data(path_normalization),
                    "commit": commit,
                },
            )
        rel = target.relative_to(context.workspace).as_posix()
        artifacts.append(rel)
        normalization_note = ""
        if path_normalization.changed:
            normalization_note = f" 路径别名已归一：{path_normalization.original_path} -> {path_normalization.normalized_path}。"
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=f"已写入并完成物理落盘验真：{rel}，字符数：{len(content)}，字节数：{commit.get('byte_size')}.{normalization_note}",
            artifacts=artifacts,
            data={
                "path": rel,
                "chars": len(content),
                "normalized_host_path": normalization_public_data(path_normalization),
                "physical_commit_verified": True,
                "commit": commit,
            },
        )
    except WorkspaceViolation as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.BLOCKED, str(exc), error_code="workspace_violation")
    except OSError as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"文件写入失败：{exc}", error_code="os_error")
