"""L3 第六阶段上下文续接纯建议对象。

本模块只表达上下文保留、丢弃、压缩需求、优先级与连续性建议。
它不写上下文存储，不调用模型摘要，不做真实压缩。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


class ContextAdviceKind(str, Enum):
    UNKNOWN = "unknown"
    CARRY_OVER = "carry_over"
    RETAIN = "retain"
    DROP = "drop"
    COMPRESS_NEEDED = "compress_needed"
    PRIORITIZE = "prioritize"
    REVIEW_CONFLICT = "review_conflict"


def _ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _ensure_advisory(flag: bool, field_name: str) -> None:
    if flag is not True:
        raise ValueError(f"{field_name} must remain true")


@dataclass(frozen=True, slots=True)
class ContextCarryoverAdvice:
    advice_ref: TypedRef
    source_context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    target_context_ref: TypedRef | None = None
    advice_kind: ContextAdviceKind = ContextAdviceKind.CARRY_OVER
    value_hint: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.value_hint, "ContextCarryoverAdvice.value_hint")
        for item in self.reason_codes:
            _ensure_short_text(item, "ContextCarryoverAdvice.reason_codes", 128)
        _ensure_short_text(self.summary, "ContextCarryoverAdvice.summary")
        _ensure_advisory(self.advisory_only, "ContextCarryoverAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ContextCarryoverAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContextWindowAdvice:
    advice_ref: TypedRef
    window_ref: TypedRef | None = None
    retained_context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    dropped_context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    estimated_window_pressure: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.estimated_window_pressure, "ContextWindowAdvice.estimated_window_pressure")
        for item in self.reason_codes:
            _ensure_short_text(item, "ContextWindowAdvice.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "ContextWindowAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ContextWindowAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContextCompressionNeedAdvice:
    advice_ref: TypedRef
    context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    compression_need_hint: float = 0.0
    suggested_method_hint: str = "future_summary_or_compaction"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.compression_need_hint, "ContextCompressionNeedAdvice.compression_need_hint")
        _ensure_short_text(self.suggested_method_hint, "ContextCompressionNeedAdvice.suggested_method_hint", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "ContextCompressionNeedAdvice.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "ContextCompressionNeedAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ContextCompressionNeedAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContextRetentionAdvice:
    advice_ref: TypedRef
    context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    retention_value_hint: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.retention_value_hint, "ContextRetentionAdvice.retention_value_hint")
        for item in self.reason_codes:
            _ensure_short_text(item, "ContextRetentionAdvice.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "ContextRetentionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ContextRetentionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContextDropAdvice:
    advice_ref: TypedRef
    context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    drop_suitability_hint: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.drop_suitability_hint, "ContextDropAdvice.drop_suitability_hint")
        for item in self.reason_codes:
            _ensure_short_text(item, "ContextDropAdvice.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "ContextDropAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ContextDropAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContextPriorityAdvice:
    advice_ref: TypedRef
    context_scores: tuple[tuple[TypedRef, float], ...] = field(default_factory=tuple)
    top_context_ref: TypedRef | None = None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for _context_ref, score in self.context_scores:
            _ensure_unit_interval(score, "ContextPriorityAdvice.context_scores score")
        for item in self.reason_codes:
            _ensure_short_text(item, "ContextPriorityAdvice.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "ContextPriorityAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ContextPriorityAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContextConflictAdvice:
    advice_ref: TypedRef
    conflicting_context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    review_hint: str = "future_context_review"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.review_hint, "ContextConflictAdvice.review_hint", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "ContextConflictAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "ContextConflictAdvice.confidence")
        _ensure_advisory(self.advisory_only, "ContextConflictAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ContextConflictAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContextStateTransitionAdvice:
    advice_ref: TypedRef
    context_ref: TypedRef
    suggested_status: str = "ready_for_carryover"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.suggested_status, "ContextStateTransitionAdvice.suggested_status", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "ContextStateTransitionAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "ContextStateTransitionAdvice.confidence")
        _ensure_advisory(self.advisory_only, "ContextStateTransitionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ContextStateTransitionAdvice.schema_version cannot be empty")
