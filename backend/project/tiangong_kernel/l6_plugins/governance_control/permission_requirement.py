"""Permission requirement declarations for L6 phase5 governance-control."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import GovernanceArtifactBase, GovernanceReasonKind, RiskTier, ensure_bool, ensure_ref_items, ensure_ref_text, ensure_score


@dataclass(frozen=True)
class PermissionRequirement(GovernanceArtifactBase):
    object_ref: str = "permission:l6_phase5_requirement"
    risk_level: RiskTier | str = RiskTier.A3
    requirement_only: bool = True
    permit_issued: bool = False
    authorization_granted: bool = False
    final_policy_result: bool = False
    l5_review_required: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "risk_level", RiskTier(self.risk_level))
        for field_name in ("requirement_only", "permit_issued", "authorization_granted", "final_policy_result", "l5_review_required"):
            ensure_bool(getattr(self, field_name), f"PermissionRequirement.{field_name}")
        if not self.requirement_only or self.permit_issued or self.authorization_granted or self.final_policy_result or not self.l5_review_required:
            raise ValueError("PermissionRequirement is not authorization or final policy")


@dataclass(frozen=True)
class HumanGateRequirement(GovernanceArtifactBase):
    object_ref: str = "requirement:l6_phase5_human_gate"
    governance_reason_ref: str = "policy:l6_phase5_hard_boundary_or_a4_review"
    confirmation_ticket_issued: bool = False
    user_confirmation_claimed: bool = False
    prompt_hint_only: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.governance_reason_ref, "HumanGateRequirement.governance_reason_ref")
        for field_name in ("confirmation_ticket_issued", "user_confirmation_claimed", "prompt_hint_only"):
            ensure_bool(getattr(self, field_name), f"HumanGateRequirement.{field_name}")
        if self.confirmation_ticket_issued or self.user_confirmation_claimed or not self.prompt_hint_only:
            raise ValueError("HumanGateRequirement cannot issue or claim confirmation")


@dataclass(frozen=True)
class ConfirmationNeedHint(GovernanceArtifactBase):
    object_ref: str = "hint:l6_phase5_confirmation_need"
    reason_kind: GovernanceReasonKind | str = GovernanceReasonKind.SYSTEM_BOUNDARY
    minimal_confirmation_preferred: bool = True
    blocks_continuation_without_l5: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "reason_kind", GovernanceReasonKind(self.reason_kind))
        ensure_bool(self.minimal_confirmation_preferred, "ConfirmationNeedHint.minimal_confirmation_preferred")
        ensure_bool(self.blocks_continuation_without_l5, "ConfirmationNeedHint.blocks_continuation_without_l5")
        if not self.minimal_confirmation_preferred or self.blocks_continuation_without_l5:
            raise ValueError("ConfirmationNeedHint should support minimal confirmation, not direct blocking")


@dataclass(frozen=True)
class MinimalConfirmationPolicy(GovernanceArtifactBase):
    object_ref: str = "policy:l6_phase5_minimal_confirmation"
    batch_safe_confirmations: bool = True
    defer_low_risk_confirmation: bool = True
    ask_every_step: bool = False
    hard_boundary_exceptions: tuple[str, ...] = field(default_factory=lambda: ("policy:a5", "policy:credential", "policy:irreversible"))

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("batch_safe_confirmations", "defer_low_risk_confirmation", "ask_every_step"):
            ensure_bool(getattr(self, field_name), f"MinimalConfirmationPolicy.{field_name}")
        ensure_ref_items(self.hard_boundary_exceptions, "MinimalConfirmationPolicy.hard_boundary_exceptions", required=True)
        if not self.batch_safe_confirmations or not self.defer_low_risk_confirmation or self.ask_every_step:
            raise ValueError("MinimalConfirmationPolicy must reduce safe interruptions")


@dataclass(frozen=True)
class ConfirmationBatchingSuggestion(GovernanceArtifactBase):
    object_ref: str = "suggestion:l6_phase5_confirmation_batching"
    batch_when_safe: bool = True
    prompt_count_estimate: int = 1
    bypass_hard_boundaries: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_bool(self.batch_when_safe, "ConfirmationBatchingSuggestion.batch_when_safe")
        if not isinstance(self.prompt_count_estimate, int) or self.prompt_count_estimate < 0:
            raise ValueError("prompt_count_estimate must be non-negative int")
        ensure_bool(self.bypass_hard_boundaries, "ConfirmationBatchingSuggestion.bypass_hard_boundaries")
        if not self.batch_when_safe or self.bypass_hard_boundaries:
            raise ValueError("Confirmation batching must be safe and preserve hard boundaries")


@dataclass(frozen=True)
class ConfirmationDeferralSuggestion(GovernanceArtifactBase):
    object_ref: str = "suggestion:l6_phase5_confirmation_deferral"
    deferral_allowed_for_low_risk: bool = True
    deferral_confidence: float = 0.8
    defers_hard_boundary: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_bool(self.deferral_allowed_for_low_risk, "ConfirmationDeferralSuggestion.deferral_allowed_for_low_risk")
        ensure_score(self.deferral_confidence, "ConfirmationDeferralSuggestion.deferral_confidence")
        ensure_bool(self.defers_hard_boundary, "ConfirmationDeferralSuggestion.defers_hard_boundary")
        if not self.deferral_allowed_for_low_risk or self.defers_hard_boundary:
            raise ValueError("Deferral applies only to safe low-risk cases")
