"""L6.72.54 工作模式失败契约。

该模块只把 work 模式的 Provider / Activation / Planner / ToolPlan 失败
转成可审计 execution_report，不调用模型、不执行工具、不绕过 PromptIntegrator。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from tiangong_agent_shell.safe_logging import redact_text

from .activation_protocol import ActivationForm
from .model_planner import ModelPlannerResult
from .public_projection_bridge import RuntimeProjection
from .tool_invocation import ToolInvocation

WORK_FAILURE_STATUSES = {
    "provider_not_ready",
    "model_required",
    "plan_repair",
    "plan_repair_failed",
    "deterministic_fallback",
    "failed_recoverable",
    "partial_with_resume",
    "completed_with_warnings",
    "blocked_A5",
    "awaiting_confirmation",
}

DETERMINISTIC_FALLBACK_TOOLS = {
    "list_dir",
    "read_file",
    "file_sha256",
    "write_workspace_file",
    "safe_command_runner",
    "create_zip_package",
}


@dataclass(frozen=True)
class WorkExecutionReport:
    status: str
    failure_kind: str = ""
    provider_status: str = ""
    plan_repair_attempted: bool = False
    deterministic_fallback_used: bool = False
    user_visible_summary: str = ""
    next_action: str = ""

    def projection(self, *, audit_count: int = 0, artifacts: Iterable[str] | None = None, chain: dict[str, Any] | None = None, pending_confirmations: list[dict[str, Any]] | None = None) -> RuntimeProjection:
        return RuntimeProjection(
            status=self.status,
            summary=self.user_visible_summary,
            artifacts=list(artifacts or []),
            audit_count=audit_count,
            chain=dict(chain or {}),
            pending_confirmations=list(pending_confirmations or []),
        )

    def public_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "failure_kind": self.failure_kind,
            "provider_status": self.provider_status,
            "plan_repair_attempted": self.plan_repair_attempted,
            "deterministic_fallback_used": self.deterministic_fallback_used,
            "final_output_contract": "execution_report",
            "user_visible_summary": self.user_visible_summary,
            "next_action": self.next_action,
        }


def plan_is_deterministic_fallback_safe(plan: list[ToolInvocation]) -> bool:
    return bool(plan) and all(str(item.tool_name) in DETERMINISTIC_FALLBACK_TOOLS for item in plan)


def build_work_execution_report(
    *,
    planner_result: ModelPlannerResult | None = None,
    activation_form: ActivationForm | None = None,
    provider_ready: bool | None = None,
    deterministic_plan_available: bool = False,
    deterministic_fallback_used: bool = False,
    tool_failed: bool = False,
    completed_with_warnings: bool = False,
    message: str = "",
) -> WorkExecutionReport:
    """把 work 模式异常转成固定 execution_report 元数据。"""
    failure_kind = infer_failure_kind(
        planner_result=planner_result,
        activation_form=activation_form,
        provider_ready=provider_ready,
        tool_failed=tool_failed,
        completed_with_warnings=completed_with_warnings,
    )
    plan_repair_attempted = bool(getattr(planner_result, "repair_attempted", False))
    provider_status = "ready" if provider_ready else "provider_not_ready" if provider_ready is False else "unknown"

    if deterministic_fallback_used:
        return WorkExecutionReport(
            status="deterministic_fallback",
            failure_kind=failure_kind or "deterministic_fallback",
            provider_status=provider_status,
            plan_repair_attempted=plan_repair_attempted,
            deterministic_fallback_used=True,
            user_visible_summary="工作模式已使用确定性回退执行可验证的本地任务；完整步骤和证据在任务工作台。",
            next_action="verify_artifacts_and_report",
        )

    if activation_form is not None and str(getattr(activation_form, "risk_level", "")).upper() == "A5":
        return WorkExecutionReport(
            status="blocked_A5",
            failure_kind="a5_blocked",
            provider_status=provider_status,
            plan_repair_attempted=plan_repair_attempted,
            user_visible_summary="工作模式已阻断：ActivationForm 判定为 A5 极高危，必须人工确认后才能继续。",
            next_action="await_user_confirmation",
        )

    if activation_form is not None and bool(getattr(activation_form, "need_user_confirm", False)):
        return WorkExecutionReport(
            status="awaiting_confirmation",
            failure_kind="confirmation_required",
            provider_status=provider_status,
            plan_repair_attempted=plan_repair_attempted,
            user_visible_summary="工作模式等待人工确认：详细风险与工具参数已进入任务工作台。",
            next_action="await_user_confirmation",
        )

    if provider_ready is False and not deterministic_plan_available:
        return WorkExecutionReport(
            status="provider_not_ready",
            failure_kind="provider_not_ready",
            provider_status=provider_status,
            plan_repair_attempted=plan_repair_attempted,
            user_visible_summary=(
                "工作模式未执行：当前 Provider / API Key / 模型未配置或不可用。"
                "此任务无法仅靠确定性规则安全完成；请配置可用模型后续接，或改成明确的本地读写/打包指令。"
            ),
            next_action="configure_provider_or_resume_with_deterministic_task",
        )

    if failure_kind == "plan_repair_failed":
        return WorkExecutionReport(
            status="failed_recoverable",
            failure_kind="plan_repair_failed",
            provider_status=provider_status,
            plan_repair_attempted=True,
            user_visible_summary="工作模式未执行：模型计划 JSON 修复失败。任务已记录为可恢复失败，详情在任务工作台。",
            next_action="retry_with_short_json_or_single_step_choice_form",
        )

    if failure_kind in {"weak_model_not_allowed", "model_policy_disabled", "tool_plan_blocked_by_model_policy"}:
        return WorkExecutionReport(
            status="model_required",
            failure_kind=failure_kind,
            provider_status=provider_status,
            plan_repair_attempted=plan_repair_attempted,
            user_visible_summary="工作模式未执行：当前模型画像不允许作为主脑执行该任务，或其工具计划超出主动模型策略边界。请切换更强模型或缩小为子任务。",
            next_action="switch_model_or_reduce_to_micro_task",
        )

    if failure_kind == "activation_chat_or_no_tools":
        return WorkExecutionReport(
            status="model_required",
            failure_kind=failure_kind,
            provider_status=provider_status,
            plan_repair_attempted=plan_repair_attempted,
            user_visible_summary="工作模式未执行：主脑本轮未激活工具链。系统不会退回普通聊天，任务已记录为需要重新规划。",
            next_action="retry_activation_with_work_contract",
        )

    if tool_failed:
        return WorkExecutionReport(
            status="failed_recoverable",
            failure_kind=failure_kind or "tool_failed",
            provider_status=provider_status,
            plan_repair_attempted=plan_repair_attempted,
            user_visible_summary="工作模式执行未完全通过：至少一个工具步骤失败。已记录失败摘要和可续接方向。",
            next_action="classify_failure_or_resume",
        )

    if completed_with_warnings:
        return WorkExecutionReport(
            status="completed_with_warnings",
            failure_kind="quality_gate_warning",
            provider_status=provider_status,
            plan_repair_attempted=plan_repair_attempted,
            user_visible_summary="工作模式已完成但存在非 A5 警告；完整质量门信息在任务工作台。",
            next_action="review_warnings_or_accept_delivery",
        )

    fallback_message = message or (getattr(planner_result, "message", "") if planner_result is not None else "")
    return WorkExecutionReport(
        status="failed_recoverable",
        failure_kind=failure_kind or "planner_failed",
        provider_status=provider_status,
        plan_repair_attempted=plan_repair_attempted,
        user_visible_summary="工作模式未执行：" + redact_text(fallback_message or "未生成可执行计划。")[:700],
        next_action="plan_repair_or_resume",
    )


def infer_failure_kind(
    *,
    planner_result: ModelPlannerResult | None = None,
    activation_form: ActivationForm | None = None,
    provider_ready: bool | None = None,
    tool_failed: bool = False,
    completed_with_warnings: bool = False,
) -> str:
    if completed_with_warnings:
        return "quality_gate_warning"
    if tool_failed:
        return "tool_failed"
    if provider_ready is False:
        return "provider_not_ready"
    if activation_form is not None:
        if str(getattr(activation_form, "risk_level", "")).upper() == "A5":
            return "a5_blocked"
        if bool(getattr(activation_form, "need_user_confirm", False)):
            return "confirmation_required"
        if str(getattr(activation_form, "mode", "chat")) == "chat" or not bool(getattr(activation_form, "tools_requested", False)):
            return "activation_chat_or_no_tools"
    if planner_result is not None:
        explicit = str(getattr(planner_result, "failure_kind", "") or "").strip()
        if explicit:
            return explicit
        message = str(getattr(planner_result, "message", "") or "").lower()
        if "a5" in message:
            return "a5_blocked"
        if "provider" in message or "model_client" in message or "model_config" in message:
            return "provider_not_ready"
        if "invalid_json" in message or "json" in message:
            return "plan_invalid_json"
    return "planner_failed"
