"""审计型虚拟返回适配器。

用于 L6.32 P1：当模型在纯代码/纯分析任务中输出可展示正文时，
Planner 将其归一为 return_code / return_analysis。该适配器只把内容作为
受治理结果返回，不执行、不写文件、不注册 Skill/Tool、不触网。
"""

from __future__ import annotations

from ..result_normalizer import truncate_text
from ..tool_invocation import ToolInvocation
from ..tool_result import ToolResult, ToolResultStatus
from ..turn_context import TurnContext


def return_code_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
    content = str(invocation.arguments.get("content") or "")
    language = str(invocation.arguments.get("language") or "text")
    task = str(invocation.arguments.get("task") or "")
    summary = content if content else "<空代码返回>"
    return ToolResult(
        step_id=invocation.step_id,
        tool_name=invocation.tool_name,
        status=ToolResultStatus.OK,
        output_summary=truncate_text(summary, context.policy.max_output_chars),
        data={
            "kind": "code",
            "language": language,
            "task_preview": truncate_text(task, 500),
            "content_chars": len(content),
            "audit_only": True,
            "executes_code": False,
            "writes_file": False,
        },
    )


def return_analysis_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
    content = str(invocation.arguments.get("content") or "")
    task = str(invocation.arguments.get("task") or "")
    summary = content if content else "<空分析返回>"
    return ToolResult(
        step_id=invocation.step_id,
        tool_name=invocation.tool_name,
        status=ToolResultStatus.OK,
        output_summary=truncate_text(summary, context.policy.max_output_chars),
        data={
            "kind": "analysis",
            "task_preview": truncate_text(task, 500),
            "content_chars": len(content),
            "audit_only": True,
            "writes_file": False,
        },
    )
