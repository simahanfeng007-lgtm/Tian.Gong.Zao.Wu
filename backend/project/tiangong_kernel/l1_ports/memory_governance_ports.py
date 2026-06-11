"""L1 记忆与遗忘治理端口协议。

本模块只定义 retention、decay、suppression、pruning、revision、tombstone、
privacy review 的请求/响应与端口协议，不执行召回、遗忘、删除或隐私处理。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.trace import TraceContext

from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class MemoryGovernanceRequest:
    """记忆治理请求。"""

    request_ref: TypedRef
    memory_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    retention_boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    privacy_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    request_only: bool = True
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if self.request_only is not True:
            raise ValueError("MemoryGovernanceRequest.request_only must remain true")
        if not self.schema_version:
            raise ValueError("MemoryGovernanceRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MemoryGovernanceResponse:
    """记忆治理响应。"""

    response_ref: TypedRef
    governance_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    response_only: bool = True
    performs_governance: bool = False
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if self.response_only is not True:
            raise ValueError("MemoryGovernanceResponse.response_only must remain true")
        if self.performs_governance:
            raise ValueError("MemoryGovernanceResponse cannot perform governance")
        if not self.schema_version:
            raise ValueError("MemoryGovernanceResponse.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ForgettingGovernanceRequest:
    """遗忘治理请求。"""

    request_ref: TypedRef
    forgetting_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    deletion_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    tombstone_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    request_only: bool = True
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if self.request_only is not True:
            raise ValueError("ForgettingGovernanceRequest.request_only must remain true")
        if not self.schema_version:
            raise ValueError("ForgettingGovernanceRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ForgettingGovernanceResponse:
    """遗忘治理响应。"""

    response_ref: TypedRef
    review_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    response_only: bool = True
    executes_forgetting: bool = False
    deletes_memory: bool = False
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if self.response_only is not True:
            raise ValueError("ForgettingGovernanceResponse.response_only must remain true")
        if self.executes_forgetting:
            raise ValueError("ForgettingGovernanceResponse cannot execute forgetting")
        if self.deletes_memory:
            raise ValueError("ForgettingGovernanceResponse cannot delete memory")
        if not self.schema_version:
            raise ValueError("ForgettingGovernanceResponse.schema_version cannot be empty")


class MemoryGovernancePort(ABC):
    """记忆治理端口协议。"""

    @abstractmethod
    def describe_memory_governance(self, request: MemoryGovernanceRequest, trace: TraceContext) -> PortResult[MemoryGovernanceResponse]:
        """描述记忆治理引用。"""


class ForgettingGovernancePort(ABC):
    """遗忘治理端口协议。"""

    @abstractmethod
    def describe_forgetting_governance(self, request: ForgettingGovernanceRequest, trace: TraceContext) -> PortResult[ForgettingGovernanceResponse]:
        """描述遗忘治理引用。"""
