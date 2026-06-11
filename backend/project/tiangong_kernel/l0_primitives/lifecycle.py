"""L0 生命周期事实原语，只表达阶段、状态、原因、策略与迁移引用；不管理进程或服务生命周期。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .identity import RefId, TypedRef


class LifecycleState(str, Enum):
    """LifecycleState 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    PROPOSED = "proposed"
    CREATED = "created"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    DEGRADED = "degraded"
    BLOCKED = "blocked"
    RECOVERING = "recovering"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATING = "terminating"
    TERMINATED = "terminated"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"
    REVOKED = "revoked"
    QUARANTINED = "quarantined"
    DELETED = "deleted"
    UNKNOWN = "unknown"


class LifecyclePhase(str, Enum):
    """LifecyclePhase 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    BIRTH = "birth"
    ACTIVATION = "activation"
    OPERATION = "operation"
    ADAPTATION = "adaptation"
    RECOVERY = "recovery"
    DECLINE = "decline"
    TERMINATION = "termination"
    ARCHIVAL = "archival"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class LifecycleRef:
    """LifecycleRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    state: LifecycleState = LifecycleState.UNKNOWN
    phase: LifecyclePhase = LifecyclePhase.UNKNOWN
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("LifecycleRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class LifecycleTransitionRef:
    """LifecycleTransitionRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    from_state: LifecycleState = LifecycleState.UNKNOWN
    to_state: LifecycleState = LifecycleState.UNKNOWN
    subject_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("LifecycleTransitionRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class LifecycleReason:
    """LifecycleReason 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    code: str
    evidence_ref: TypedRef | None = None

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("LifecycleReason.code cannot be empty")


@dataclass(frozen=True, slots=True)
class LifecyclePolicyRef:
    """LifecyclePolicyRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    policy_type: str = "unknown"
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.policy_type:
            raise ValueError("LifecyclePolicyRef.policy_type cannot be empty")
        if not self.schema_version:
            raise ValueError("LifecyclePolicyRef.schema_version cannot be empty")
