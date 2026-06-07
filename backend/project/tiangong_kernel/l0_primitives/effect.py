"""L0 副作用事实原语，只表达副作用类别、边界、影响与结果引用；不产生真实副作用。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class EffectKind(str, Enum):
    """EffectKind 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    SEND = "send"
    MODIFY_STATE = "modify_state"
    ALLOCATE_RESOURCE = "allocate_resource"
    RELEASE_RESOURCE = "release_resource"
    SPAWN = "spawn"
    TERMINATE = "terminate"
    OBSERVE = "observe"
    UNKNOWN = "unknown"


class EffectState(str, Enum):
    """EffectState 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    AUTHORIZED = "authorized"
    REJECTED = "rejected"
    LEASED = "leased"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    COMPENSATED = "compensated"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class EffectReversibility(str, Enum):
    """EffectReversibility 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    REVERSIBLE = "reversible"
    COMPENSATABLE = "compensatable"
    IRREVERSIBLE = "irreversible"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class EffectRef:
    """EffectRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    kind: EffectKind = EffectKind.UNKNOWN
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("EffectRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EffectResultRef:
    """EffectResultRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    result_type: str = "unknown"
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.result_type:
            raise ValueError("EffectResultRef.result_type cannot be empty")
        if not self.schema_version:
            raise ValueError("EffectResultRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EffectImpact:
    """EffectImpact 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    level: str = "unknown"
    description_ref: TypedRef | None = None

    def __post_init__(self) -> None:
        if not self.level:
            raise ValueError("EffectImpact.level cannot be empty")


@dataclass(frozen=True, slots=True)
class EffectBoundaryRef:
    """EffectBoundaryRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    boundary_type: str = "unknown"
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.boundary_type:
            raise ValueError("EffectBoundaryRef.boundary_type cannot be empty")
        if not self.schema_version:
            raise ValueError("EffectBoundaryRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EffectIntent:
    """EffectIntent 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    effect_ref: EffectRef
    kind: EffectKind
    state: EffectState = EffectState.PROPOSED
    target_ref: TypedRef | None = None
    result_ref: EffectResultRef | None = None
    reversibility: EffectReversibility = EffectReversibility.UNKNOWN
    impact: EffectImpact = field(default_factory=EffectImpact)
    boundary_ref: EffectBoundaryRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("EffectIntent.schema_version cannot be empty")
