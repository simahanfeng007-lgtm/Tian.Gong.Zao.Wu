"""L6.17 工程诊断 adapter。"""

from __future__ import annotations

from ..diagnostic_bridge import EngineeringDiagnosticBridge
from ..project_index_bridge import ProjectIndexBridge
from ..tool_invocation import ToolInvocation
from ..tool_result import ToolResult, ToolResultStatus
from ..turn_context import TurnContext
from ..workspace_guard import WorkspaceViolation


def build_diagnose_project_adapter(project_index: ProjectIndexBridge, diagnostic_bridge: EngineeringDiagnosticBridge):
    def diagnose_project_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        path = str(invocation.arguments.get("path") or ".")
        max_depth = int(invocation.arguments.get("max_depth") or 6)
        max_files = int(invocation.arguments.get("max_files") or 1500)
        try:
            snapshot = project_index.snapshot or project_index.scan(context.workspace, path=path, max_depth=max_depth, max_files=max_files)
            diagnosis = diagnostic_bridge.diagnose(snapshot)
        except WorkspaceViolation as exc:
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.BLOCKED, str(exc), error_code="workspace_violation")
        except OSError as exc:
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"工程诊断失败：{exc}", error_code="os_error")
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=diagnosis.summary_text(),
            data=diagnosis.public_dict(),
        )

    return diagnose_project_adapter
