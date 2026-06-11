"""L3 编排请求对象，包装 L1 信封与 L2 状态引用。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l1_ports.envelope import CommandEnvelope, PortRequest, QueryEnvelope

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION, OrchestrationIdentity
from .orchestration_status import OrchestrationStatus


class OrchestrationRequestKind(str, Enum):
    """编排请求类别。"""

    UNKNOWN = "unknown"
    PLAN_DRAFT = "plan_draft"
    MATH_ASSESSMENT = "math_assessment"
    ROUTE_RANKING = "route_ranking"
    STATE_TRANSITION_ADVICE = "state_transition_advice"


@dataclass(frozen=True, slots=True)
class OrchestrationRequest:
    """L3 编排请求。

    作用：保存进入 L3 的请求身份、L1 信封、L2 状态引用和摘要。
    边界：不调用端口，不解析真实载荷，不触发状态写入。
    """

    identity: OrchestrationIdentity
    status: OrchestrationStatus
    request_kind: OrchestrationRequestKind = OrchestrationRequestKind.UNKNOWN
    inbound_request: PortRequest | None = None
    command_envelope: CommandEnvelope | None = None
    query_envelope: QueryEnvelope | None = None
    l2_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    projection_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    goal_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    constraint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.summary) > 512:
            raise ValueError("OrchestrationRequest.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("OrchestrationRequest.schema_version cannot be empty")
