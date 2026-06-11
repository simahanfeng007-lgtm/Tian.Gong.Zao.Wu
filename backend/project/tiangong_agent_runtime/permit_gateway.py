"""Permit 裁决。"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from .execution_policy import ExecutionPolicy, PermitStatus, RiskLevel
from .tool_invocation import ToolInvocation


@dataclass(frozen=True)
class PermitDecision:
    status: PermitStatus
    risk_level: RiskLevel
    message: str
    ticket_id: str = ""

    @property
    def allowed(self) -> bool:
        return self.status is PermitStatus.ALLOWED


class PermitGateway:
    def __init__(self, policy: ExecutionPolicy | None = None) -> None:
        self.policy = policy or ExecutionPolicy.default()

    def decide(self, invocation: ToolInvocation, risk_level: RiskLevel, reason: str = "") -> PermitDecision:
        status = self.policy.dynamic_status(risk_level)
        if status is PermitStatus.BLOCKED:
            return PermitDecision(
                status=PermitStatus.BLOCKED,
                risk_level=risk_level,
                message=f"{risk_level.value} 已被生物动态策略阻断：{reason or '高危操作'}",
            )
        if status is PermitStatus.CONFIRMATION_REQUIRED:
            return PermitDecision(
                status=PermitStatus.CONFIRMATION_REQUIRED,
                risk_level=risk_level,
                message=f"{risk_level.value} 需要用户确认：{reason or invocation.tool_name}",
                ticket_id=f"confirm_{uuid4().hex[:12]}",
            )
        return PermitDecision(
            status=PermitStatus.ALLOWED,
            risk_level=risk_level,
            message=f"{risk_level.value} 已按 L6.72.39 执行力优先策略放行；仅 A5 硬拦。",
        )
