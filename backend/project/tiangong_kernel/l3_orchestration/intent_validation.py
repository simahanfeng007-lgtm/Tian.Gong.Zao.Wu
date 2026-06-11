"""L3 第四阶段意图校验与缺口建议对象。

本模块只输出校验建议、缺口、冲突、澄清、拒绝、降级和重试路径建议。
它不调用模型，不调用工具，不执行降级或拒绝动作。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .intent_envelope import IntentKind
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_lifecycle import LifecycleTransitionIntent, OrchestrationLifecycleKind


class IntentValidationKind(str, Enum):
    """意图校验建议类别。"""

    UNKNOWN = "unknown"
    STRUCTURE = "structure"
    MISSING_FIELD = "missing_field"
    CONFLICT = "conflict"
    AMBIGUITY = "ambiguity"
    CLARIFICATION_QUESTION = "clarification_question"
    REJECT_PATH = "reject_path"
    DEGRADE_PATH = "degrade_path"
    RETRY_PATH = "retry_path"
    STATE_TRANSITION = "state_transition"


def _ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True)
class IntentStructureValidationResult:
    """意图结构校验结果；不代表准入裁决。"""

    result_ref: TypedRef
    intent_ref: TypedRef
    intent_kind: IntentKind = IntentKind.UNKNOWN
    valid_structure_hint: bool = False
    provided_fields: tuple[str, ...] = field(default_factory=tuple)
    missing_fields: tuple[str, ...] = field(default_factory=tuple)
    conflict_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    validation_score: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.provided_fields + self.missing_fields:
            _ensure_short_text(item, "IntentStructureValidationResult fields", 128)
        _ensure_unit_interval(self.validation_score, "IntentStructureValidationResult.validation_score")
        _ensure_short_text(self.reason_summary, "IntentStructureValidationResult.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("IntentStructureValidationResult.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("IntentStructureValidationResult.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IntentValidationAdvice:
    """意图校验总建议；不触发任何动作。"""

    advice_ref: TypedRef
    validation_result: IntentStructureValidationResult
    advice_kind: IntentValidationKind = IntentValidationKind.STRUCTURE
    suggested_path_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.confidence, "IntentValidationAdvice.confidence")
        _ensure_short_text(self.reason_summary, "IntentValidationAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("IntentValidationAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("IntentValidationAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IntentMissingFieldAdvice:
    """意图缺字段建议。"""

    advice_ref: TypedRef
    intent_ref: TypedRef
    missing_field_names: tuple[str, ...] = field(default_factory=tuple)
    priority: float = 0.0
    clarification_hint: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.missing_field_names:
            _ensure_short_text(item, "IntentMissingFieldAdvice.missing_field_names", 128)
        _ensure_unit_interval(self.priority, "IntentMissingFieldAdvice.priority")
        _ensure_short_text(self.clarification_hint, "IntentMissingFieldAdvice.clarification_hint")
        if self.advisory_only is not True:
            raise ValueError("IntentMissingFieldAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("IntentMissingFieldAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IntentConflictAdvice:
    """意图冲突建议；不做裁决。"""

    advice_ref: TypedRef
    intent_ref: TypedRef
    conflict_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    conflict_score: float = 0.0
    resolution_hint: str = "review_conflict_before_progress"
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.conflict_score, "IntentConflictAdvice.conflict_score")
        _ensure_short_text(self.resolution_hint, "IntentConflictAdvice.resolution_hint")
        if self.advisory_only is not True:
            raise ValueError("IntentConflictAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("IntentConflictAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IntentAmbiguityAdvice:
    """通用意图歧义建议。"""

    advice_ref: TypedRef
    intent_ref: TypedRef
    ambiguity_score: float = 0.0
    ambiguous_field_names: tuple[str, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.ambiguity_score, "IntentAmbiguityAdvice.ambiguity_score")
        for item in self.ambiguous_field_names:
            _ensure_short_text(item, "IntentAmbiguityAdvice.ambiguous_field_names", 128)
        _ensure_short_text(self.reason_summary, "IntentAmbiguityAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("IntentAmbiguityAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("IntentAmbiguityAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IntentClarificationQuestionAdvice:
    """澄清问题建议；不自动向用户发送。"""

    advice_ref: TypedRef
    intent_ref: TypedRef
    question_hints: tuple[str, ...] = field(default_factory=tuple)
    related_missing_fields: tuple[str, ...] = field(default_factory=tuple)
    priority: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.question_hints + self.related_missing_fields:
            _ensure_short_text(item, "IntentClarificationQuestionAdvice short fields", 256)
        _ensure_unit_interval(self.priority, "IntentClarificationQuestionAdvice.priority")
        if self.advisory_only is not True:
            raise ValueError("IntentClarificationQuestionAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("IntentClarificationQuestionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IntentRejectPathAdvice:
    """拒绝路径建议；不执行拒绝动作。"""

    advice_ref: TypedRef
    intent_ref: TypedRef
    reject_reason_codes: tuple[str, ...] = field(default_factory=tuple)
    safe_alternative_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reject_score: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.reject_reason_codes:
            _ensure_short_text(item, "IntentRejectPathAdvice.reject_reason_codes", 128)
        _ensure_unit_interval(self.reject_score, "IntentRejectPathAdvice.reject_score")
        _ensure_short_text(self.reason_summary, "IntentRejectPathAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("IntentRejectPathAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("IntentRejectPathAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IntentDegradePathAdvice:
    """降级路径建议；不执行降级动作。"""

    advice_ref: TypedRef
    intent_ref: TypedRef
    degrade_target_hint: str = "clarify_or_reduce_scope"
    degrade_score: float = 0.0
    preserved_context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.degrade_target_hint, "IntentDegradePathAdvice.degrade_target_hint", 128)
        _ensure_unit_interval(self.degrade_score, "IntentDegradePathAdvice.degrade_score")
        _ensure_short_text(self.reason_summary, "IntentDegradePathAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("IntentDegradePathAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("IntentDegradePathAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IntentRetryPathAdvice:
    """重试路径建议；不执行重试。"""

    advice_ref: TypedRef
    intent_ref: TypedRef
    retry_condition_hints: tuple[str, ...] = field(default_factory=tuple)
    retry_score: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.retry_condition_hints:
            _ensure_short_text(item, "IntentRetryPathAdvice.retry_condition_hints", 128)
        _ensure_unit_interval(self.retry_score, "IntentRetryPathAdvice.retry_score")
        _ensure_short_text(self.reason_summary, "IntentRetryPathAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("IntentRetryPathAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("IntentRetryPathAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IntentStateTransitionSuggestion:
    """通用意图状态转移建议；不写入 L2。"""

    suggestion_ref: TypedRef
    intent_ref: TypedRef
    intent_kind: IntentKind = IntentKind.UNKNOWN
    current_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.CREATED
    suggested_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.PREPARED
    transition_intent: LifecycleTransitionIntent = LifecycleTransitionIntent.CONTINUE_CURRENT_STEP
    transition_score: float = 0.0
    validation_advice_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.transition_score, "IntentStateTransitionSuggestion.transition_score")
        _ensure_short_text(self.reason_summary, "IntentStateTransitionSuggestion.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("IntentStateTransitionSuggestion.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("IntentStateTransitionSuggestion.schema_version cannot be empty")
