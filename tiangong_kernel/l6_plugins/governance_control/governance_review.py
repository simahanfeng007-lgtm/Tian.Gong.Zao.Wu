"""Unified governance review request declarations for L6 phase5."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import GovernanceArtifactBase, GovernanceReviewTarget, GovernanceReasonKind, ensure_bool, ensure_ref_items, ensure_ref_text


@dataclass(frozen=True)
class GovernanceReasonRef(GovernanceArtifactBase):
    object_ref: str = "ref:l6_phase5_governance_reason"
    reason_kind: GovernanceReasonKind | str = GovernanceReasonKind.SYSTEM_BOUNDARY
    reason_ref: str = "policy:l6_phase5_governance_reason"
    synthetic_reason_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "reason_kind", GovernanceReasonKind(self.reason_kind))
        ensure_ref_text(self.reason_ref, "GovernanceReasonRef.reason_ref")
        ensure_bool(self.synthetic_reason_allowed, "GovernanceReasonRef.synthetic_reason_allowed")
        if self.synthetic_reason_allowed:
            raise ValueError("Governance reason must not be synthetic")


@dataclass(frozen=True)
class GovernanceReviewRequest(GovernanceArtifactBase):
    object_ref: str = "request:l6_phase5_governance_review"
    target: GovernanceReviewTarget | str = GovernanceReviewTarget.L5_REVIEW
    risk_projection_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase5_risk",))
    permission_requirement_refs: tuple[str, ...] = field(default_factory=lambda: ("permission:l6_phase5_requirement",))
    budget_requirement_refs: tuple[str, ...] = field(default_factory=lambda: ("budget:l6_phase5_requirement",))
    audit_requirement_refs: tuple[str, ...] = field(default_factory=lambda: ("audit:l6_phase5_requirement",))
    credential_requirement_refs: tuple[str, ...] = field(default_factory=lambda: ("credential-policy:l6_phase5_requirement_ref",))
    privacy_requirement_refs: tuple[str, ...] = field(default_factory=lambda: ("requirement:l6_phase5_redaction",))
    ref_only: bool = True
    final_decision: bool = False
    dispatches_review: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "target", GovernanceReviewTarget(self.target))
        for field_name in (
            "risk_projection_refs", "permission_requirement_refs", "budget_requirement_refs", "audit_requirement_refs",
            "credential_requirement_refs", "privacy_requirement_refs",
        ):
            ensure_ref_items(getattr(self, field_name), f"GovernanceReviewRequest.{field_name}", required=True)
        for field_name in ("ref_only", "final_decision", "dispatches_review"):
            ensure_bool(getattr(self, field_name), f"GovernanceReviewRequest.{field_name}")
        if not self.ref_only or self.final_decision or self.dispatches_review:
            raise ValueError("GovernanceReviewRequest is ref-only and non-dispatching")


@dataclass(frozen=True)
class GovernanceReviewBundle(GovernanceArtifactBase):
    object_ref: str = "summary:l6_phase5_governance_review_bundle"
    request_refs: tuple[str, ...] = field(default_factory=lambda: ("request:l6_phase5_governance_review",))
    l5_final_review_required: bool = True
    final_result_included: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.request_refs, "GovernanceReviewBundle.request_refs", required=True)
        ensure_bool(self.l5_final_review_required, "GovernanceReviewBundle.l5_final_review_required")
        ensure_bool(self.final_result_included, "GovernanceReviewBundle.final_result_included")
        if not self.l5_final_review_required or self.final_result_included:
            raise ValueError("Governance review bundle cannot include final result")


@dataclass(frozen=True)
class L3GovernanceContinuationHint(GovernanceArtifactBase):
    object_ref: str = "l3:l6_phase5_governance_continuation_hint"
    continuation_preferred: bool = True
    requires_l3_scheduling: bool = True
    self_schedules: bool = False
    summary_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase5_governance_continuation",))

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("continuation_preferred", "requires_l3_scheduling", "self_schedules"):
            ensure_bool(getattr(self, field_name), f"L3GovernanceContinuationHint.{field_name}")
        ensure_ref_items(self.summary_refs, "L3GovernanceContinuationHint.summary_refs", required=True)
        if not self.continuation_preferred or not self.requires_l3_scheduling or self.self_schedules:
            raise ValueError("L3 continuation hint cannot self-schedule")


@dataclass(frozen=True)
class L5GovernanceReviewHint(GovernanceArtifactBase):
    object_ref: str = "l5:l6_phase5_review_hint"
    l5_review_required: bool = True
    l6_finalizes_review: bool = False
    review_reason_refs: tuple[str, ...] = field(default_factory=lambda: ("policy:l6_phase5_governance_review",))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_bool(self.l5_review_required, "L5GovernanceReviewHint.l5_review_required")
        ensure_bool(self.l6_finalizes_review, "L5GovernanceReviewHint.l6_finalizes_review")
        ensure_ref_items(self.review_reason_refs, "L5GovernanceReviewHint.review_reason_refs", required=True)
        if not self.l5_review_required or self.l6_finalizes_review:
            raise ValueError("L5GovernanceReviewHint must leave final review to L5")


@dataclass(frozen=True)
class GovernanceDecisionPlaceholder(GovernanceArtifactBase):
    object_ref: str = "placeholder:l6_phase5_waiting_l5_governance"
    waits_for_l5: bool = True
    is_final_governance_result: bool = False
    grants_or_denies: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("waits_for_l5", "is_final_governance_result", "grants_or_denies"):
            ensure_bool(getattr(self, field_name), f"GovernanceDecisionPlaceholder.{field_name}")
        if not self.waits_for_l5 or self.is_final_governance_result or self.grants_or_denies:
            raise ValueError("GovernanceDecisionPlaceholder is not a decision")
