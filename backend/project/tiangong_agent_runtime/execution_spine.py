"""受治理执行脊柱。"""

from __future__ import annotations

from tiangong_agent_shell.tool_bridge import ToolExecutionMode

from .audit_bridge import AuditBridge
from .confirmation_ticket import ConfirmationTicketStore
from .error_mapper import failed_result
from .execution_policy import PermitStatus
from .permit_gateway import PermitGateway
from .risk_classifier import RiskClassifier
from .runtime_tool_registry import RuntimeToolRegistry
from .tool_invocation import ToolInvocation
from .tool_result import ToolResult, ToolResultStatus
from .turn_context import TurnContext


class ExecutionSpine:
    def __init__(
        self,
        registry: RuntimeToolRegistry,
        audit: AuditBridge | None = None,
        ticket_store: ConfirmationTicketStore | None = None,
    ) -> None:
        self.registry = registry
        self.audit = audit or AuditBridge()
        self.ticket_store = ticket_store or ConfirmationTicketStore()
        self.risk_classifier = RiskClassifier()

    def execute_plan(self, context: TurnContext, plan: list[ToolInvocation]) -> list[ToolResult]:
        if context.tool_mode is ToolExecutionMode.DISABLED:
            return [
                ToolResult(
                    step_id=invocation.step_id,
                    tool_name=invocation.tool_name,
                    status=ToolResultStatus.BLOCKED,
                    output_summary="工具执行模式 disabled：未执行真实工具。",
                    error_code="tool_mode_disabled",
                )
                for invocation in plan
            ]

        results: list[ToolResult] = []
        gateway = PermitGateway(context.policy)
        for invocation in plan[: context.max_steps]:
            risk_level, reason = self.risk_classifier.classify(invocation)
            invocation = invocation.with_risk(risk_level, reason)
            decision = gateway.decide(invocation, risk_level, reason)
            if decision.status is PermitStatus.BLOCKED:
                result = ToolResult(
                    step_id=invocation.step_id,
                    tool_name=invocation.tool_name,
                    status=ToolResultStatus.BLOCKED,
                    output_summary=decision.message,
                    error_code="permit_blocked",
                )
                audit_ref = self.audit.record(invocation, risk_level=risk_level, permit_status=decision.status, result=result)
                results.append(_with_audit_ref(result, audit_ref))
                break
            if decision.status is PermitStatus.CONFIRMATION_REQUIRED:
                ticket = self.ticket_store.create(
                    ticket_id=decision.ticket_id,
                    invocation=invocation,
                    risk_level=risk_level,
                    reason=reason,
                    message=decision.message,
                )
                result = ToolResult(
                    step_id=invocation.step_id,
                    tool_name=invocation.tool_name,
                    status=ToolResultStatus.CONFIRMATION_REQUIRED,
                    output_summary=f"{decision.message} ticket_id={decision.ticket_id}",
                    error_code="confirmation_required",
                    data={"ticket_id": decision.ticket_id, "ticket": ticket.to_public_dict()},
                )
                audit_ref = self.audit.record(invocation, risk_level=risk_level, permit_status=decision.status, result=result)
                results.append(_with_audit_ref(result, audit_ref))
                break

            result = self._execute_allowed_invocation(context, invocation, permit_status=decision.status)
            results.append(result)
            if result.status in {ToolResultStatus.BLOCKED, ToolResultStatus.CONFIRMATION_REQUIRED}:
                break
        return results

    def execute_confirmed_ticket(self, context: TurnContext, ticket_id: str) -> ToolResult:
        """执行已确认票据。

        用户确认只替代 PermitGateway 的 A4 暂停，不替代 registry、adapter、workspace guard、
        command allowlist 或 audit。若 adapter 仍判定越界，结果仍会 blocked/failed。
        """
        ticket = self.ticket_store.confirm(ticket_id)
        if ticket is None:
            return ToolResult(
                step_id=f"confirm_{ticket_id}",
                tool_name="confirm_ticket",
                status=ToolResultStatus.FAILED,
                output_summary="确认票据不存在、已处理或已过期。",
                error_code="ticket_not_pending",
            )
        invocation = ticket.invocation.with_risk(ticket.risk_level, ticket.reason or "用户已确认。")
        return self._execute_allowed_invocation(context, invocation, permit_status=PermitStatus.ALLOWED)

    def _execute_allowed_invocation(
        self,
        context: TurnContext,
        invocation: ToolInvocation,
        *,
        permit_status: PermitStatus,
    ) -> ToolResult:
        risk_level = invocation.risk_level or self.risk_classifier.classify(invocation)[0]
        adapter = self.registry.get(invocation.tool_name)
        if adapter is None:
            result = failed_result(invocation.step_id, invocation.tool_name, "工具未注册，拒绝执行。", code="tool_not_registered")
        elif context.tool_mode is ToolExecutionMode.DRY_RUN:
            result = ToolResult(
                step_id=invocation.step_id,
                tool_name=invocation.tool_name,
                status=ToolResultStatus.SKIPPED,
                output_summary="dry_run：计划已通过治理链，但未执行真实 adapter。",
                data={"arguments": invocation.arguments, "risk_level": risk_level.value},
            )
        else:
            result = adapter(invocation, context)
        audit_ref = self.audit.record(invocation, risk_level=risk_level, permit_status=permit_status, result=result)
        return _with_audit_ref(result, audit_ref)


def _with_audit_ref(result: ToolResult, audit_ref: str) -> ToolResult:
    return ToolResult(
        step_id=result.step_id,
        tool_name=result.tool_name,
        status=result.status,
        output_summary=result.output_summary,
        data=dict(result.data),
        artifacts=list(result.artifacts),
        error_code=result.error_code,
        audit_ref=audit_ref,
    )
