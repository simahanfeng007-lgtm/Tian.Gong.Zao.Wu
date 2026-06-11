"""受治理模型聊天适配器。

L6.13 将普通聊天的模型调用纳入 Runtime 执行链：
RiskClassifier → PermitGateway → RuntimeToolRegistry → model_chat_adapter → AuditBridge。

注意：真实 messages/model_config/model_client 放在 TurnContext 中，不放在 ToolInvocation.arguments，
避免审计、报告、公共投影泄露完整 prompt 或 API Key。
"""

from __future__ import annotations

from tiangong_agent_shell.errors import AgentShellError
from tiangong_agent_shell.safe_logging import redact_text
from tiangong_agent_shell.prompt_compiler import compile_existing_messages_envelope
from tiangong_agent_shell.model_client_port import ensure_compiled_prompt_envelope

from ..tool_invocation import ToolInvocation
from ..tool_result import ToolResult, ToolResultStatus
from ..turn_context import TurnContext


def model_chat_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
    if context.model_client is None or context.model_config is None:
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.FAILED,
            output_summary="模型运行上下文缺失：model_client/model_config 未装配。",
            error_code="model_context_missing",
        )
    try:
        envelope = ensure_compiled_prompt_envelope(context.compiled_prompt)
    except Exception as exc:
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.FAILED,
            output_summary=f"模型运行上下文缺失：必须由 PromptIntegrator 提供 CompiledPromptEnvelope（{type(exc).__name__}）。",
            error_code="compiled_prompt_missing",
        )
    try:
        chat_result = context.model_client.chat(envelope, context.model_config)
    except ValueError as exc:
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.FAILED,
            output_summary=f"模型调用被 PromptIntegrator 边界拒绝：{exc}",
            error_code="compiled_prompt_required",
        )
    except AgentShellError as exc:
        api_key = str(getattr(context.model_config, "api_key", "") or "")
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.FAILED,
            output_summary=redact_text(exc.user_message, [api_key]),
            error_code="model_client_error",
            data={"provider": getattr(context.model_config, "provider", ""), "detail": redact_text(exc.detail, [api_key])},
        )
    except Exception as exc:  # noqa: BLE001 - adapter boundary must convert all failures to ToolResult
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.FAILED,
            output_summary="模型调用失败：出现未分类异常。",
            error_code="model_unclassified_error",
            data={"error_type": type(exc).__name__},
        )

    content = str(chat_result.content)
    return ToolResult(
        step_id=invocation.step_id,
        tool_name=invocation.tool_name,
        status=ToolResultStatus.OK,
        output_summary=f"模型调用完成：provider={chat_result.provider} model={chat_result.model} chars={len(content)}",
        data={
            "provider": chat_result.provider,
            "model": chat_result.model,
            "content": content,
            "content_chars": len(content),
        },
    )
