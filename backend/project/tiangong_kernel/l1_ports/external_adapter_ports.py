"""L1 外部适配器表面端口声明。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.trace import TraceContext

from .port_result import PortResult


REQUIRED_EXTERNAL_ADAPTER_PORT_SURFACES = (
    "model",
    "tool",
    "file",
    "network",
    "terminal",
    "desktop",
    "database",
    "browser",
    "git",
    "build",
    "test",
    "sandbox",
    "storage",
)


@dataclass(frozen=True, slots=True)
class ExternalAdapterPortBoundary:
    """外部适配器端口边界，声明授权、审计、凭证、预算和沙箱引用。"""

    boundary_ref: TypedRef
    surface: str
    effect_ref: TypedRef | None = None
    lease_ref: TypedRef | None = None
    decision_ref: TypedRef | None = None
    event_ref: TypedRef | None = None
    audit_ref: TypedRef | None = None
    credential_ref: TypedRef | None = None
    resource_budget_ref: TypedRef | None = None
    sandbox_policy_ref: TypedRef | None = None
    supported_modes: tuple[str, ...] = ("disabled", "fake", "dry_run", "no_op")
    capability_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ExternalAdapterActionRequest:
    """外部适配动作请求，只描述动作表面和边界引用。"""

    request_ref: TypedRef
    surface: str
    boundary_ref: TypedRef
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ExternalAdapterActionResponse:
    """外部适配动作响应，只返回结果或失败引用。"""

    response_ref: TypedRef
    surface: str
    result_ref: TypedRef | None = None
    failure_ref: TypedRef | None = None
    schema_version: str = "0.1"


class ExternalAdapterPort(ABC):
    """外部适配器边界端口，不执行真实适配。"""

    @abstractmethod
    def declare_adapter_boundary(self, boundary: ExternalAdapterPortBoundary, trace: TraceContext) -> PortResult[ExternalAdapterPortBoundary]:
        raise NotImplementedError


class ExternalAdapterActionPort(ABC):
    """外部适配动作端口，不触发真实外部动作。"""

    @abstractmethod
    def submit_adapter_action(self, request: ExternalAdapterActionRequest, trace: TraceContext) -> PortResult[ExternalAdapterActionResponse]:
        raise NotImplementedError
