"""Python 质量检查适配器。"""

from __future__ import annotations

import subprocess
import sys

from ..result_normalizer import truncate_text
from ..tool_invocation import ToolInvocation
from ..tool_result import ToolResult, ToolResultStatus
from ..turn_context import TurnContext
from ..workspace_guard import WorkspaceGuard, WorkspaceViolation


ALLOWED_COMMANDS = {"compileall", "python -m compileall", "pytest", "python -m pytest"}


def run_python_quality_check_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
    command = str(invocation.arguments.get("command") or invocation.arguments.get("command_type") or "compileall").strip().lower()
    target = str(invocation.arguments.get("target") or ".")
    timeout = float(invocation.arguments.get("timeout") or context.policy.default_timeout_seconds)
    guard = WorkspaceGuard(context.workspace)
    try:
        safe_target = guard.resolve_for_read(target)
    except WorkspaceViolation as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.BLOCKED, str(exc), error_code="workspace_violation")

    if command not in ALLOWED_COMMANDS:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.BLOCKED, "命令不在 Python 质量检查 allowlist。", error_code="command_not_allowed")

    if "compileall" in command:
        argv = [sys.executable, "-m", "compileall", str(safe_target)]
    else:
        argv = [sys.executable, "-m", "pytest", str(safe_target), "-q"]

    try:
        completed = subprocess.run(  # noqa: S603 - argv is allowlisted and shell=False
            argv,
            cwd=str(context.workspace),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return ToolResult(
            invocation.step_id,
            invocation.tool_name,
            ToolResultStatus.FAILED,
            f"质量检查超时：{timeout} 秒。",
            error_code="timeout",
            data={"stdout": truncate_text(exc.stdout or ""), "stderr": truncate_text(exc.stderr or "")},
        )

    output = "\n".join(part for part in [completed.stdout, completed.stderr] if part)
    status = ToolResultStatus.OK if completed.returncode == 0 else ToolResultStatus.FAILED
    return ToolResult(
        step_id=invocation.step_id,
        tool_name=invocation.tool_name,
        status=status,
        output_summary=truncate_text(output or f"命令退出码：{completed.returncode}", context.policy.max_output_chars),
        error_code="" if completed.returncode == 0 else "quality_check_failed",
        data={"returncode": completed.returncode, "argv": argv},
    )
