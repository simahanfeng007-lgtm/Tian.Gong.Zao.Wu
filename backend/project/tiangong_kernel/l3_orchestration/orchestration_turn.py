"""L3 第二阶段 Turn 编排对象。

Turn 对象只保存轮次顺序、上下文续接提示和连续性评估引用，不做真实上下文拼接。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_lifecycle import OrchestrationLifecycleKind


class TurnCarryoverKind(str, Enum):
    """Turn 间可续接信息类别。"""

    UNKNOWN = "unknown"
    GOAL = "goal"
    CONSTRAINT = "constraint"
    USER_PREFERENCE = "user_preference"
    MISSING_STATE = "missing_state"
    PARTIAL_RESULT = "partial_result"
    BLOCKER = "blocker"
    RECOVERY_NOTE = "recovery_note"


@dataclass(frozen=True, slots=True)
class TurnOrchestrationRef:
    """Turn 编排引用。"""

    turn_ref: TypedRef
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    turn_index: int = 0
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.turn_index < 0:
            raise ValueError("TurnOrchestrationRef.turn_index cannot be negative")
        if not self.schema_version:
            raise ValueError("TurnOrchestrationRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class TurnSequenceRef:
    """Turn 序列引用事实。"""

    sequence_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    turn_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    current_turn_ref: TypedRef | None = None
    previous_turn_ref: TypedRef | None = None
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.current_turn_ref is not None and self.turn_refs and self.current_turn_ref not in self.turn_refs:
            raise ValueError("TurnSequenceRef.current_turn_ref must be included in turn_refs")
        if self.previous_turn_ref is not None and self.turn_refs and self.previous_turn_ref not in self.turn_refs:
            raise ValueError("TurnSequenceRef.previous_turn_ref must be included in turn_refs")
        if not self.schema_version:
            raise ValueError("TurnSequenceRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class TurnCarryoverHint:
    """Turn 间上下文续接提示。

    边界：只表达续接价值和引用，不拼接真实上下文，不读取记忆，不检索。
    """

    hint_ref: TypedRef | None = None
    carryover_kind: TurnCarryoverKind = TurnCarryoverKind.UNKNOWN
    source_turn_ref: TypedRef | None = None
    target_turn_ref: TypedRef | None = None
    related_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    carryover_value: float = 0.0
    confidence: float = 0.0
    advisory_only: bool = True
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.carryover_value <= 1.0:
            raise ValueError("TurnCarryoverHint.carryover_value must be between 0.0 and 1.0")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("TurnCarryoverHint.confidence must be between 0.0 and 1.0")
        if self.advisory_only is not True:
            raise ValueError("TurnCarryoverHint.advisory_only must remain true in L3 phase 2")
        if len(self.summary) > 512:
            raise ValueError("TurnCarryoverHint.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("TurnCarryoverHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class TurnContinuityEvaluation:
    """Turn 连续性评估事实。"""

    evaluation_ref: TypedRef | None = None
    sequence_ref: TypedRef | None = None
    carryover_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    context_carryover_score_ref: TypedRef | None = None
    context_carryover_score_value: float = 0.0
    confidence: float = 0.0
    advisory_only: bool = True
    reason_summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.context_carryover_score_value <= 1.0:
            raise ValueError("TurnContinuityEvaluation.context_carryover_score_value must be between 0.0 and 1.0")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("TurnContinuityEvaluation.confidence must be between 0.0 and 1.0")
        if self.advisory_only is not True:
            raise ValueError("TurnContinuityEvaluation.advisory_only must remain true in L3 phase 2")
        if len(self.reason_summary) > 512:
            raise ValueError("TurnContinuityEvaluation.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("TurnContinuityEvaluation.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class TurnOrchestrationPlan:
    """Turn 编排计划事实。"""

    plan_ref: TypedRef | None = None
    turn_ref: TurnOrchestrationRef | None = None
    lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.UNKNOWN
    sequence_ref: TurnSequenceRef | None = None
    carryover_hints: tuple[TurnCarryoverHint, ...] = field(default_factory=tuple)
    continuity_evaluation_ref: TypedRef | None = None
    future_l6_context_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.advisory_only is not True:
            raise ValueError("TurnOrchestrationPlan.advisory_only must remain true in L3 phase 2")
        if len(self.summary) > 512:
            raise ValueError("TurnOrchestrationPlan.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("TurnOrchestrationPlan.schema_version cannot be empty")
