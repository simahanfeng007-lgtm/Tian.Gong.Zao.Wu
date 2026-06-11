"""Requirement clarification candidates for L6 phase6."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import ProductArtifactBase, ensure_bool, ensure_ref_items


@dataclass(frozen=True)
class ProductClarificationCandidate(ProductArtifactBase):
    object_ref: str = "product:l6_phase6_clarification_candidate"
    question_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_minimal_question",))
    mandatory_now: bool = False
    can_continue_with_assumption: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.question_refs, "ProductClarificationCandidate.question_refs", required=True)
        ensure_bool(self.mandatory_now, "ProductClarificationCandidate.mandatory_now")
        ensure_bool(self.can_continue_with_assumption, "ProductClarificationCandidate.can_continue_with_assumption")
        if self.mandatory_now and self.can_continue_with_assumption:
            raise ValueError("clarification cannot be both mandatory immediately and safely skippable")


@dataclass(frozen=True)
class RequirementGapReport(ProductArtifactBase):
    object_ref: str = "report:l6_phase6_requirement_gap"
    gap_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_gap",))
    low_risk_assumable: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.gap_refs, "RequirementGapReport.gap_refs", required=True)
        ensure_bool(self.low_risk_assumable, "RequirementGapReport.low_risk_assumable")


@dataclass(frozen=True)
class RequirementConflictReport(ProductArtifactBase):
    object_ref: str = "report:l6_phase6_requirement_conflict"
    conflict_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_requirement_conflict",))
    hard_blocking: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.conflict_refs, "RequirementConflictReport.conflict_refs", required=True)
        ensure_bool(self.hard_blocking, "RequirementConflictReport.hard_blocking")


@dataclass(frozen=True)
class MinimalQuestionSuggestion(ProductArtifactBase):
    object_ref: str = "suggestion:l6_phase6_minimal_question"
    question_batch_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_question_batch",))
    asks_only_when_blocking: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.question_batch_refs, "MinimalQuestionSuggestion.question_batch_refs", required=True)
        ensure_bool(self.asks_only_when_blocking, "MinimalQuestionSuggestion.asks_only_when_blocking")
        if not self.asks_only_when_blocking:
            raise ValueError("MinimalQuestionSuggestion must avoid over-clarification")


@dataclass(frozen=True)
class ContinueWithoutClarificationHint(ProductArtifactBase):
    object_ref: str = "hint:l6_phase6_continue_without_clarification"
    assumption_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_safe_default_assumption",))
    safe_to_continue: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.assumption_refs, "ContinueWithoutClarificationHint.assumption_refs", required=True)
        ensure_bool(self.safe_to_continue, "ContinueWithoutClarificationHint.safe_to_continue")
        if not self.safe_to_continue:
            raise ValueError("ContinueWithoutClarificationHint must mean safe continuation")
