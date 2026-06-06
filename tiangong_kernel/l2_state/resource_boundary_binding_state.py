"""L2 资源边界绑定状态对象。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class ResourceBoundaryBindingStatus(str, Enum):
    """资源边界绑定状态枚举，表示活跃、近限、耗尽、限流、降级或暂停。"""

    ACTIVE = "active"
    NEAR_LIMIT = "near_limit"
    EXHAUSTED = "exhausted"
    THROTTLED = "throttled"
    DEGRADED = "degraded"
    PAUSED = "paused"


@dataclass(frozen=True, slots=True)
class ResourceBoundaryBindingState:
    """资源边界绑定状态，关联预算、配额、限流和压力状态引用。"""

    identity: L2StateIdentity
    status: L2StateStatus
    subject_kind: str
    subject_ref: TypedRef
    budget_state_ref: TypedRef | None = None
    quota_state_ref: TypedRef | None = None
    rate_limit_state_ref: TypedRef | None = None
    resource_pressure_state_ref: TypedRef | None = None
    binding_status: ResourceBoundaryBindingStatus = ResourceBoundaryBindingStatus.ACTIVE
    metadata: L2StateMetadata | None = None
    state_only: bool = True
    consumes_resource: bool = False
    schema_version: str = L2_STATE_SCHEMA_VERSION
