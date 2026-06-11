"""L1 审批与人工门协议端口。

本模块只定义 approval/human gate 的请求、响应和端口协议，不签发确认票据，
不做人类审批结论，不调用上层系统。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .port_result import PortResult


APPROVAL_HUMAN_GATE_PORT_SCHEMA_VERSION = "0.1"


@dataclass(frozen=True, slots=True)
class ApprovalRequest:
    """审批请求协议对象，只保存引用。"""

    request_ref: TypedRef | None = None
    action_intent_ref: TypedRef | None = None
    boundary_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    request_only: bool = True
    schema_version: str = APPROVAL_HUMAN_GATE_PORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.request_only is not True:
            raise ValueError("ApprovalRequest.request_only must remain true")
        if not self.schema_version:
            raise ValueError("ApprovalRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ApprovalResponse:
    """审批响应协议对象，只保存未来审批引用。"""

    response_ref: TypedRef | None = None
    approval_result_ref: TypedRef | None = None
    denial_reason_ref: TypedRef | None = None
    response_only: bool = True
    grants_permission: bool = False
    issues_ticket: bool = False
    schema_version: str = APPROVAL_HUMAN_GATE_PORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.response_only is not True:
            raise ValueError("ApprovalResponse.response_only must remain true")
        if self.grants_permission:
            raise ValueError("ApprovalResponse cannot grant permission")
        if self.issues_ticket:
            raise ValueError("ApprovalResponse cannot issue tickets")
        if not self.schema_version:
            raise ValueError("ApprovalResponse.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class HumanGateRequest:
    """人工门请求协议对象，只表达等待与恢复引用。"""

    request_ref: TypedRef | None = None
    approval_request_ref: TypedRef | None = None
    wait_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    resume_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    request_only: bool = True
    schema_version: str = APPROVAL_HUMAN_GATE_PORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.request_only is not True:
            raise ValueError("HumanGateRequest.request_only must remain true")
        if not self.schema_version:
            raise ValueError("HumanGateRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class HumanGateResponse:
    """人工门响应协议对象，只表达引用，不确认。"""

    response_ref: TypedRef | None = None
    human_gate_result_ref: TypedRef | None = None
    response_only: bool = True
    confirms_action: bool = False
    schema_version: str = APPROVAL_HUMAN_GATE_PORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.response_only is not True:
            raise ValueError("HumanGateResponse.response_only must remain true")
        if self.confirms_action:
            raise ValueError("HumanGateResponse cannot confirm actions")
        if not self.schema_version:
            raise ValueError("HumanGateResponse.schema_version cannot be empty")


class ApprovalBoundaryPort(ABC):
    """审批边界端口协议，只定义调用形状。"""

    @abstractmethod
    def request_approval(self, request: ApprovalRequest) -> PortResult[ApprovalResponse]:
        """请求未来审批边界，返回引用结果。"""


class HumanGateBoundaryPort(ABC):
    """人工门边界端口协议，只定义调用形状。"""

    @abstractmethod
    def request_human_gate(self, request: HumanGateRequest) -> PortResult[HumanGateResponse]:
        """请求未来人工门边界，返回引用结果。"""
