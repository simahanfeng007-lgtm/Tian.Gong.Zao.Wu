"""L1 合同与约束引用协议端口。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .port_result import PortResult


CONTRACT_CONSTRAINT_PORT_SCHEMA_VERSION = "0.1"


@dataclass(frozen=True, slots=True)
class ContractReferenceRequest:
    """合同引用请求协议对象。"""

    request_ref: TypedRef | None = None
    action_intent_ref: TypedRef | None = None
    contract_candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    request_only: bool = True
    schema_version: str = CONTRACT_CONSTRAINT_PORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.request_only is not True:
            raise ValueError("ContractReferenceRequest.request_only must remain true")
        if not self.schema_version:
            raise ValueError("ContractReferenceRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContractReferenceResponse:
    """合同引用响应协议对象。"""

    response_ref: TypedRef | None = None
    contract_binding_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    response_only: bool = True
    contract_decision_made: bool = False
    schema_version: str = CONTRACT_CONSTRAINT_PORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.response_only is not True:
            raise ValueError("ContractReferenceResponse.response_only must remain true")
        if self.contract_decision_made:
            raise ValueError("ContractReferenceResponse cannot decide contract outcomes")
        if not self.schema_version:
            raise ValueError("ContractReferenceResponse.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ConstraintCheckRequest:
    """约束检查请求协议对象。"""

    request_ref: TypedRef | None = None
    action_intent_ref: TypedRef | None = None
    constraint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    request_only: bool = True
    schema_version: str = CONTRACT_CONSTRAINT_PORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.request_only is not True:
            raise ValueError("ConstraintCheckRequest.request_only must remain true")
        if not self.schema_version:
            raise ValueError("ConstraintCheckRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ConstraintCheckResponse:
    """约束检查响应协议对象，只保存约束结果引用。"""

    response_ref: TypedRef | None = None
    constraint_result_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    response_only: bool = True
    grants_permission: bool = False
    schema_version: str = CONTRACT_CONSTRAINT_PORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.response_only is not True:
            raise ValueError("ConstraintCheckResponse.response_only must remain true")
        if self.grants_permission:
            raise ValueError("ConstraintCheckResponse cannot grant permission")
        if not self.schema_version:
            raise ValueError("ConstraintCheckResponse.schema_version cannot be empty")


class ContractReferencePort(ABC):
    """合同引用端口协议。"""

    @abstractmethod
    def request_contract_reference(self, request: ContractReferenceRequest) -> PortResult[ContractReferenceResponse]:
        """请求未来合同引用。"""


class ConstraintCheckPort(ABC):
    """约束检查端口协议。"""

    @abstractmethod
    def request_constraint_check(self, request: ConstraintCheckRequest) -> PortResult[ConstraintCheckResponse]:
        """请求未来约束检查引用。"""
