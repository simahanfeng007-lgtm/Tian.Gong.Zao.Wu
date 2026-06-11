"""确认票据存储。

L6.12 口径：确认票据不是第二条执行通道，只保存被 PermitGateway 暂停的
ToolInvocation 安全摘要与原始受控调用对象。用户确认后仍必须回到
ExecutionSpine 的 registry/adapter/audit 链路执行。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from time import time
from typing import Any

from tiangong_agent_shell.safe_logging import sanitize_mapping

from .execution_policy import RiskLevel
from .tool_invocation import ToolInvocation


class ConfirmationTicketStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DENIED = "denied"


@dataclass(frozen=True)
class ConfirmationTicket:
    ticket_id: str
    invocation: ToolInvocation
    risk_level: RiskLevel
    reason: str = ""
    message: str = ""
    status: ConfirmationTicketStatus = ConfirmationTicketStatus.PENDING
    created_at: float = field(default_factory=time)
    resolved_at: float = 0.0

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "ticket_id": self.ticket_id,
            "tool_name": self.invocation.tool_name,
            "step_id": self.invocation.step_id,
            "risk_level": self.risk_level.value,
            "reason": self.reason,
            "message": self.message,
            "status": self.status.value,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
            "arguments": sanitize_mapping(self.invocation.arguments),
        }

    def mark(self, status: ConfirmationTicketStatus) -> "ConfirmationTicket":
        return ConfirmationTicket(
            ticket_id=self.ticket_id,
            invocation=self.invocation,
            risk_level=self.risk_level,
            reason=self.reason,
            message=self.message,
            status=status,
            created_at=self.created_at,
            resolved_at=time(),
        )


class ConfirmationTicketStore:
    """内存态确认票据表。

    第一版只做进程内票据，避免把可执行请求持久化到包体或磁盘。
    后续若持久化，必须加过期时间、签名、脱敏与用户确认二次校验。
    """

    def __init__(self) -> None:
        self._tickets: dict[str, ConfirmationTicket] = {}

    def create(
        self,
        *,
        ticket_id: str,
        invocation: ToolInvocation,
        risk_level: RiskLevel,
        reason: str = "",
        message: str = "",
    ) -> ConfirmationTicket:
        ticket = ConfirmationTicket(
            ticket_id=ticket_id,
            invocation=invocation,
            risk_level=risk_level,
            reason=reason,
            message=message,
        )
        self._tickets[ticket_id] = ticket
        return ticket

    def get(self, ticket_id: str) -> ConfirmationTicket | None:
        return self._tickets.get(ticket_id)

    def pending(self) -> list[ConfirmationTicket]:
        return [ticket for ticket in self._tickets.values() if ticket.status is ConfirmationTicketStatus.PENDING]

    def confirm(self, ticket_id: str) -> ConfirmationTicket | None:
        ticket = self._tickets.get(ticket_id)
        if ticket is None or ticket.status is not ConfirmationTicketStatus.PENDING:
            return None
        updated = ticket.mark(ConfirmationTicketStatus.CONFIRMED)
        self._tickets[ticket_id] = updated
        return updated

    def deny(self, ticket_id: str) -> ConfirmationTicket | None:
        ticket = self._tickets.get(ticket_id)
        if ticket is None or ticket.status is not ConfirmationTicketStatus.PENDING:
            return None
        updated = ticket.mark(ConfirmationTicketStatus.DENIED)
        self._tickets[ticket_id] = updated
        return updated

    def public_pending(self) -> list[dict[str, Any]]:
        return [ticket.to_public_dict() for ticket in self.pending()]

    def public_all(self) -> list[dict[str, Any]]:
        return [ticket.to_public_dict() for ticket in self._tickets.values()]
