from __future__ import annotations

from tiangong_agent_runtime.execution_policy import PermitStatus, RiskLevel
from tiangong_agent_runtime.permit_gateway import PermitGateway
from tiangong_agent_runtime.tool_invocation import ToolInvocation


def test_a1_a3_auto_execute() -> None:
    gateway = PermitGateway()
    for level in [RiskLevel.A1, RiskLevel.A3]:
        decision = gateway.decide(ToolInvocation("read_file"), level)
        assert decision.status is PermitStatus.ALLOWED


def test_a4_requires_confirmation() -> None:
    decision = PermitGateway().decide(ToolInvocation("write_workspace_file"), RiskLevel.A4, "外部路径写入")
    assert decision.status is PermitStatus.CONFIRMATION_REQUIRED
    assert decision.ticket_id.startswith("confirm_")


def test_a5_blocks() -> None:
    decision = PermitGateway().decide(ToolInvocation("unknown"), RiskLevel.A5, "未知工具")
    assert decision.status is PermitStatus.BLOCKED
    assert not decision.allowed
