"""交付 ZIP 打包适配器。"""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

from ..tool_invocation import ToolInvocation
from ..tool_result import ToolResult, ToolResultStatus
from ..turn_context import TurnContext
from ..workspace_guard import SENSITIVE_NAMES, SENSITIVE_SUFFIXES, WorkspaceGuard, WorkspaceViolation

EXCLUDE_DIRS = {
    ".git", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".linyuanzhe", "reports", ".r21_adapter_smoke_workspace",
    "document_contexts", "file_handoffs", "model_profiles", "prompt_trace", "tasks",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
EXCLUDE_NAMES = {".DS_Store"}


def create_zip_package_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
    guard = WorkspaceGuard(context.workspace)
    try:
        source = guard.resolve_for_read(invocation.arguments.get("source") or ".")
        target = guard.resolve_for_artifact(invocation.arguments.get("target") or "dist/tiangong_delivery.zip")
    except WorkspaceViolation as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.BLOCKED, str(exc), error_code="workspace_violation")

    if not source.exists():
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, "打包源不存在。", error_code="path_not_found")

    skipped: list[str] = []
    files_added = 0
    try:
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            candidates = [source] if source.is_file() else list(source.rglob("*"))
            for path in candidates:
                if path.is_dir():
                    continue
                rel = path.relative_to(source if source.is_dir() else source.parent)
                if _should_skip(path):
                    skipped.append(str(rel))
                    continue
                if target == path:
                    continue
                zf.write(path, rel.as_posix())
                files_added += 1
    except OSError as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"ZIP 打包失败：{exc}", error_code="zip_failed")

    sha256 = hashlib.sha256(target.read_bytes()).hexdigest()
    sha_path = target.with_suffix(target.suffix + ".sha256")
    sha_path.write_text(f"{sha256}  {target.name}\n", encoding="utf-8")
    rel_target = target.relative_to(context.workspace).as_posix()
    rel_sha = sha_path.relative_to(context.workspace).as_posix()
    return ToolResult(
        step_id=invocation.step_id,
        tool_name=invocation.tool_name,
        status=ToolResultStatus.OK,
        output_summary=f"已生成 ZIP：{rel_target}；文件数：{files_added}；SHA256：{sha256}",
        artifacts=[rel_target, rel_sha],
        data={"sha256": sha256, "files_added": files_added, "skipped": skipped[:50]},
    )


def _should_skip(path: Path) -> bool:
    lowered_parts = {part.lower() for part in path.parts}
    if lowered_parts.intersection(EXCLUDE_DIRS):
        return True
    if path.name in EXCLUDE_NAMES or path.name.lower() in SENSITIVE_NAMES:
        return True
    if path.suffix.lower() in EXCLUDE_SUFFIXES or path.suffix.lower() in SENSITIVE_SUFFIXES:
        return True
    lowered = path.as_posix().lower()
    return any(term in lowered for term in ["secret", "token", "credential", "api_key"])
