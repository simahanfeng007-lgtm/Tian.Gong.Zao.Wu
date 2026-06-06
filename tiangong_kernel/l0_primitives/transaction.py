"""L0 事务事实原语，只表达事务、提交、回滚、补偿与幂等键引用；不执行事务、不回滚资源。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class ReversibilityKind(str, Enum):
    """ReversibilityKind 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    IDEMPOTENT = "idempotent"
    REVERSIBLE = "reversible"
    COMPENSABLE = "compensable"
    IRREVERSIBLE = "irreversible"
    UNKNOWN = "unknown"


class TransactionKind(str, Enum):
    """TransactionKind 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    SINGLE_EFFECT = "single_effect"
    EFFECT_CHAIN = "effect_chain"
    SAGA = "saga"
    CHECKPOINTED = "checkpointed"
    HUMAN_APPROVED = "human_approved"
    RECOVERY = "recovery"
    UNKNOWN = "unknown"


class TransactionState(str, Enum):
    """TransactionState 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    PROPOSED = "proposed"
    AUTHORIZED = "authorized"
    IN_PROGRESS = "in_progress"
    PARTIALLY_COMMITTED = "partially_committed"
    COMMITTED = "committed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class CompensationState(str, Enum):
    """CompensationState 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    NOT_REQUIRED = "not_required"
    AVAILABLE = "available"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    MANUAL_REQUIRED = "manual_required"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class TransactionRef:
    """TransactionRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    kind: TransactionKind = TransactionKind.UNKNOWN
    state: TransactionState = TransactionState.UNKNOWN
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("TransactionRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CompensationRef:
    """CompensationRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    state: CompensationState = CompensationState.UNKNOWN
    target_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("CompensationRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IdempotencyKey:
    """IdempotencyKey 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: str
    scope_ref: TypedRef | None = None

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("IdempotencyKey.value cannot be empty")


@dataclass(frozen=True, slots=True)
class CommitRef:
    """CommitRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    transaction_ref: TransactionRef | None = None
    effect_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("CommitRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RollbackRef:
    """RollbackRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    transaction_ref: TransactionRef | None = None
    compensation_ref: CompensationRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("RollbackRef.schema_version cannot be empty")
