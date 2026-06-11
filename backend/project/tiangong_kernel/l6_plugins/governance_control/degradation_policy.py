"""Degradation policy declarations for L6 phase5 governance-control."""

from __future__ import annotations

from dataclasses import dataclass

from .common import GovernanceArtifactBase, ensure_bool, ensure_no_live_or_sensitive_text, ensure_ref_text


@dataclass(frozen=True)
class DegradationSuggestion(GovernanceArtifactBase):
    object_ref: str = "suggestion:l6_phase5_degradation"
    suggestion_only: bool = True
    command: bool = False
    aborts_task: bool = False
    continue_in_degraded_mode: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("suggestion_only", "command", "aborts_task", "continue_in_degraded_mode"):
            ensure_bool(getattr(self, field_name), f"DegradationSuggestion.{field_name}")
        if not self.suggestion_only or self.command or self.aborts_task or not self.continue_in_degraded_mode:
            raise ValueError("DegradationSuggestion is not a command and should continue when safe")


@dataclass(frozen=True)
class ScopeReductionSuggestion(GovernanceArtifactBase):
    object_ref: str = "suggestion:l6_phase5_scope_reduction"
    reduced_scope_summary: str = "summary:reduce_noncritical_branches"
    suggestion_only: bool = True
    hard_stop: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_no_live_or_sensitive_text(self.reduced_scope_summary, "ScopeReductionSuggestion.reduced_scope_summary")
        ensure_bool(self.suggestion_only, "ScopeReductionSuggestion.suggestion_only")
        ensure_bool(self.hard_stop, "ScopeReductionSuggestion.hard_stop")
        if not self.suggestion_only or self.hard_stop:
            raise ValueError("ScopeReductionSuggestion cannot hard stop")


@dataclass(frozen=True)
class LowEnergyModeSuggestion(GovernanceArtifactBase):
    object_ref: str = "suggestion:l6_phase5_low_energy_mode"
    low_energy_summary: str = "summary:continue_readonly_or_chunked"
    refusal: bool = False
    governance_reason_ref: str = "policy:l6_phase5_degradation_reason"

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_no_live_or_sensitive_text(self.low_energy_summary, "LowEnergyModeSuggestion.low_energy_summary")
        ensure_bool(self.refusal, "LowEnergyModeSuggestion.refusal")
        ensure_ref_text(self.governance_reason_ref, "LowEnergyModeSuggestion.governance_reason_ref")
        if self.refusal:
            raise ValueError("LowEnergyModeSuggestion is not refusal")


@dataclass(frozen=True)
class RecoverableContinuationHint(GovernanceArtifactBase):
    object_ref: str = "hint:l6_phase5_recoverable_continuation"
    recovery_possible: bool = True
    checkpoint_hint_ref: str = "ref:l6_phase5_checkpoint_hint"
    resumes_without_bypassing_l3: bool = True
    self_executes_resume: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_bool(self.recovery_possible, "RecoverableContinuationHint.recovery_possible")
        ensure_ref_text(self.checkpoint_hint_ref, "RecoverableContinuationHint.checkpoint_hint_ref")
        ensure_bool(self.resumes_without_bypassing_l3, "RecoverableContinuationHint.resumes_without_bypassing_l3")
        ensure_bool(self.self_executes_resume, "RecoverableContinuationHint.self_executes_resume")
        if not self.recovery_possible or not self.resumes_without_bypassing_l3 or self.self_executes_resume:
            raise ValueError("RecoverableContinuationHint cannot self-execute resume")


@dataclass(frozen=True)
class HumanizedGovernanceStyleHint(GovernanceArtifactBase):
    object_ref: str = "hint:l6_phase5_humanized_governance_style"
    governance_reason_ref: str = "policy:l6_phase5_real_governance_reason"
    style_summary: str = "summary:humanized_expression_after_real_governance_reason"
    creates_refusal: bool = False
    synthetic_reason_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.governance_reason_ref, "HumanizedGovernanceStyleHint.governance_reason_ref")
        ensure_no_live_or_sensitive_text(self.style_summary, "HumanizedGovernanceStyleHint.style_summary")
        ensure_bool(self.creates_refusal, "HumanizedGovernanceStyleHint.creates_refusal")
        ensure_bool(self.synthetic_reason_allowed, "HumanizedGovernanceStyleHint.synthetic_reason_allowed")
        if self.creates_refusal or self.synthetic_reason_allowed:
            raise ValueError("HumanizedGovernanceStyleHint cannot create refusal or synthetic reason")
