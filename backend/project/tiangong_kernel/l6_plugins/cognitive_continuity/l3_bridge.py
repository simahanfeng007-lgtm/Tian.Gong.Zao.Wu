"""L3 bridge parsing and conflict set declarations for phase4.

The parser object records how L3 may interpret L6 outputs after L5 review.  It
is not a scheduler and does not dispatch plans.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l6_plugins.common._common import L6_COMMON_SCHEMA_VERSION, ensure_bool, ensure_no_live_or_sensitive_text, ensure_ref_items, ensure_ref_text, ensure_schema_version, stable_digest
from .common import L6_PHASE4


@dataclass(frozen=True)
class L3CognitiveCandidateParser:
    parser_ref: str = "l3:l6_phase4_cognitive_candidate_parser"
    phase: str = L6_PHASE4
    accepted_output_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_candidate",))
    requires_l5_reviewed_input: bool = True
    emits_execution_plan: bool = False
    grants_permission: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.parser_ref, "L3CognitiveCandidateParser.parser_ref")
        if self.phase != L6_PHASE4:
            raise ValueError("L3CognitiveCandidateParser.phase must be L6 phase4")
        ensure_ref_items(self.accepted_output_refs, "L3CognitiveCandidateParser.accepted_output_refs", required=True)
        ensure_bool(self.requires_l5_reviewed_input, "L3CognitiveCandidateParser.requires_l5_reviewed_input")
        ensure_bool(self.emits_execution_plan, "L3CognitiveCandidateParser.emits_execution_plan")
        ensure_bool(self.grants_permission, "L3CognitiveCandidateParser.grants_permission")
        if not self.requires_l5_reviewed_input or self.emits_execution_plan or self.grants_permission:
            raise ValueError("L3 parser declaration is review-only and cannot emit plan or permit")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True)
class CognitiveConflictSet:
    conflict_set_ref: str = "l3:l6_phase4_cognitive_conflict_set"
    phase: str = L6_PHASE4
    conflicting_candidate_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_conflict_a", "projection:l6_phase4_conflict_b"))
    conflict_summary: str = "summary:l6_phase4_cognitive_conflict"
    auto_merge_allowed: bool = False
    l3_l5_review_required: bool = True
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.conflict_set_ref, "CognitiveConflictSet.conflict_set_ref")
        if self.phase != L6_PHASE4:
            raise ValueError("CognitiveConflictSet.phase must be L6 phase4")
        ensure_ref_items(self.conflicting_candidate_refs, "CognitiveConflictSet.conflicting_candidate_refs", required=True)
        ensure_no_live_or_sensitive_text(self.conflict_summary, "CognitiveConflictSet.conflict_summary")
        ensure_bool(self.auto_merge_allowed, "CognitiveConflictSet.auto_merge_allowed")
        ensure_bool(self.l3_l5_review_required, "CognitiveConflictSet.l3_l5_review_required")
        if self.auto_merge_allowed or not self.l3_l5_review_required:
            raise ValueError("cognitive conflict set cannot auto merge")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True)
class L3CandidateDispatchHint:
    hint_ref: str = "l3:l6_phase4_candidate_dispatch_hint"
    phase: str = L6_PHASE4
    candidate_ref: str = "projection:l6_phase4_candidate"
    next_review_ref: str = "l5:l6_phase4_governance_review"
    is_plan: bool = False
    is_permit: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in ("hint_ref", "candidate_ref", "next_review_ref"):
            ensure_ref_text(getattr(self, field_name), f"L3CandidateDispatchHint.{field_name}")
        if self.phase != L6_PHASE4:
            raise ValueError("L3CandidateDispatchHint.phase must be L6 phase4")
        ensure_bool(self.is_plan, "L3CandidateDispatchHint.is_plan")
        ensure_bool(self.is_permit, "L3CandidateDispatchHint.is_permit")
        if self.is_plan or self.is_permit:
            raise ValueError("L3 candidate dispatch hint is not plan or permit")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)
