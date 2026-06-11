"""L6.16 项目雷达只读扫描适配器。"""

from __future__ import annotations

from ..project_index_bridge import ProjectIndexBridge
from ..result_normalizer import truncate_text
from ..tool_invocation import ToolInvocation
from ..tool_result import ToolResult, ToolResultStatus
from ..turn_context import TurnContext
from ..workspace_guard import WorkspaceViolation


def build_scan_project_adapter(bridge: ProjectIndexBridge):
    def scan_project_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            snapshot = bridge.scan(
                context.workspace,
                path=invocation.arguments.get("path") or ".",
                max_depth=int(invocation.arguments.get("max_depth") or 6),
                max_files=int(invocation.arguments.get("max_files") or 1500),
            )
            return ToolResult(
                step_id=invocation.step_id,
                tool_name=invocation.tool_name,
                status=ToolResultStatus.OK,
                output_summary=truncate_text(snapshot.summary_text(), context.policy.max_output_chars),
                data=snapshot.public_dict(),
            )
        except WorkspaceViolation as exc:
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.BLOCKED, str(exc), error_code="workspace_violation")
        except (OSError, ValueError) as exc:
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"项目扫描失败：{exc}", error_code="project_scan_failed")

    return scan_project_adapter
