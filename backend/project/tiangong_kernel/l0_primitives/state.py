"""L0 状态事实原语，只表达状态、快照、检查点、约束、违规与恢复点引用；不落盘、不恢复、不推进状态机。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef
from .time import TimeRange


class StateKind(str, Enum):
    """StateKind 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    RUNTIME = "runtime"
    EXECUTION = "execution"
    SNAPSHOT = "snapshot"
    DELTA = "delta"
    CHECKPOINT = "checkpoint"
    RECOVERY_POINT = "recovery_point"
    DOMAIN = "domain"
    UNKNOWN = "unknown"


class ConstraintKind(str, Enum):
    """ConstraintKind 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    PRECONDITION = "precondition"
    POSTCONDITION = "postcondition"
    INVARIANT = "invariant"
    RESOURCE_LIMIT = "resource_limit"
    SCOPE_BOUNDARY = "scope_boundary"
    LEASE_BOUNDARY = "lease_boundary"
    CONTRACT_BOUNDARY = "contract_boundary"
    STABILITY_RANGE = "stability_range"
    UNKNOWN = "unknown"


class ViolationSeverity(str, Enum):
    """ViolationSeverity 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class RuntimeStateRef:
    """RuntimeStateRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    kind: StateKind = StateKind.RUNTIME
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("RuntimeStateRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionStateRef:
    """ExecutionStateRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    kind: StateKind = StateKind.EXECUTION
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ExecutionStateRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class StateSnapshotRef:
    """StateSnapshotRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    state_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("StateSnapshotRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class StateDeltaRef:
    """StateDeltaRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    before_ref: TypedRef | None = None
    after_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("StateDeltaRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CheckpointRef:
    """CheckpointRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    snapshot_ref: StateSnapshotRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("CheckpointRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoveryPointRef:
    """RecoveryPointRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    checkpoint_ref: CheckpointRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("RecoveryPointRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class InvariantRef:
    """InvariantRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    subject_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("InvariantRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ConstraintRef:
    """ConstraintRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    kind: ConstraintKind = ConstraintKind.UNKNOWN
    subject_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ConstraintRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class StabilityRange:
    """StabilityRange 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    label: str = "unknown"
    range: TimeRange | None = None
    lower_bound: float | None = None
    upper_bound: float | None = None

    def __post_init__(self) -> None:
        if not self.label:
            raise ValueError("StabilityRange.label cannot be empty")
        if self.lower_bound is not None and self.upper_bound is not None and self.upper_bound < self.lower_bound:
            raise ValueError("StabilityRange.upper_bound cannot be lower than lower_bound")


@dataclass(frozen=True, slots=True)
class Violation:
    """Violation 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    violation_ref: TypedRef
    severity: ViolationSeverity = ViolationSeverity.UNKNOWN
    constraint_ref: ConstraintRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("Violation.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CoreState:
    """CoreState 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    state_ref: TypedRef
    kind: StateKind = StateKind.UNKNOWN
    snapshot_ref: StateSnapshotRef | None = None
    delta_ref: StateDeltaRef | None = None
    checkpoint_ref: CheckpointRef | None = None
    recovery_point_ref: RecoveryPointRef | None = None
    invariant_refs: tuple[InvariantRef, ...] = field(default_factory=tuple)
    constraint_refs: tuple[ConstraintRef, ...] = field(default_factory=tuple)
    violations: tuple[Violation, ...] = field(default_factory=tuple)
    stability_range: StabilityRange | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("CoreState.schema_version cannot be empty")
