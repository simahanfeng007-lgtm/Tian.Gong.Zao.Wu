"""Affective projections and pressure objects for L6 phase4."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l6_plugins.common._common import L6_COMMON_SCHEMA_VERSION, ensure_bool, ensure_score, ensure_no_live_or_sensitive_text, ensure_ref_items, ensure_ref_text, ensure_schema_version, stable_digest
from ..common import CognitiveOutputKind
from ..projection import CognitiveOutputBase


def _score(value: float, field_name: str) -> None:
    ensure_score(value, field_name)


@dataclass(frozen=True)
class AffectiveProjection(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_affective_projection"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.PROJECTION
    plugin_ref: str = "l6_phase4:affective_reentry"
    modulation_layer_only: bool = True
    expression_style_score: float = 0.5
    action_tendency_score: float = 0.5
    is_fact: bool = False
    is_permission: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_bool(self.modulation_layer_only, "AffectiveProjection.modulation_layer_only")
        ensure_bool(self.is_fact, "AffectiveProjection.is_fact")
        ensure_bool(self.is_permission, "AffectiveProjection.is_permission")
        _score(self.expression_style_score, "AffectiveProjection.expression_style_score")
        _score(self.action_tendency_score, "AffectiveProjection.action_tendency_score")
        if not self.modulation_layer_only or self.is_fact or self.is_permission:
            raise ValueError("affective projection is modulation only, not fact or permission")


@dataclass(frozen=True)
class FatigueProjection(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_fatigue_projection"
    plugin_ref: str = "l6_phase4:affective_reentry"
    fatigue_score: float = 0.0
    suggested_degradation_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase4_segment_work", "summary:l6_phase4_low_energy_mode"))
    refusal_authority: bool = False
    can_refuse_without_governance: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.fatigue_score, "FatigueProjection.fatigue_score")
        ensure_ref_items(self.suggested_degradation_refs, "FatigueProjection.suggested_degradation_refs", required=True)
        ensure_bool(self.refusal_authority, "FatigueProjection.refusal_authority")
        ensure_bool(self.can_refuse_without_governance, "FatigueProjection.can_refuse_without_governance")
        if self.refusal_authority or self.can_refuse_without_governance:
            raise ValueError("fatigue projection cannot be refusal authority")


@dataclass(frozen=True)
class ResourcePressureProjection(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_resource_pressure"
    plugin_ref: str = "l6_phase4:affective_reentry"
    budget_pressure_score: float = 0.0
    context_window_pressure_score: float = 0.0
    tool_quota_pressure_score: float = 0.0
    time_cost_pressure_score: float = 0.0
    is_fatigue: bool = False
    charges_budget: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("budget_pressure_score", "context_window_pressure_score", "tool_quota_pressure_score", "time_cost_pressure_score"):
            _score(getattr(self, field_name), f"ResourcePressureProjection.{field_name}")
        ensure_bool(self.is_fatigue, "ResourcePressureProjection.is_fatigue")
        ensure_bool(self.charges_budget, "ResourcePressureProjection.charges_budget")
        if self.is_fatigue or self.charges_budget:
            raise ValueError("resource pressure is not fatigue and cannot charge budget")


@dataclass(frozen=True)
class AffectiveDegradationSuggestion(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_affective_degradation_suggestion"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.SUGGESTION
    plugin_ref: str = "l6_phase4:affective_reentry"
    degradation_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase4_segment", "summary:l6_phase4_request_scope_reduction"))
    is_command: bool = False
    is_refusal: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.degradation_refs, "AffectiveDegradationSuggestion.degradation_refs", required=True)
        ensure_bool(self.is_command, "AffectiveDegradationSuggestion.is_command")
        ensure_bool(self.is_refusal, "AffectiveDegradationSuggestion.is_refusal")
        if self.is_command or self.is_refusal:
            raise ValueError("affective degradation suggestion is not command or refusal")


@dataclass(frozen=True)
class LongTermAffectiveDriftMonitor:
    monitor_ref: str = "projection:l6_phase4_long_term_affective_drift"
    drift_score: float = 0.0
    pollution_trend_score: float = 0.0
    recovery_capacity_score: float = 0.5
    report_only: bool = True
    mutates_core_policy: bool = False
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase4_affective_drift",))
    summary: str = "summary:l6_phase4_affective_drift"
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.monitor_ref, "LongTermAffectiveDriftMonitor.monitor_ref")
        for field_name in ("drift_score", "pollution_trend_score", "recovery_capacity_score"):
            _score(getattr(self, field_name), f"LongTermAffectiveDriftMonitor.{field_name}")
        ensure_bool(self.report_only, "LongTermAffectiveDriftMonitor.report_only")
        ensure_bool(self.mutates_core_policy, "LongTermAffectiveDriftMonitor.mutates_core_policy")
        ensure_ref_items(self.evidence_refs, "LongTermAffectiveDriftMonitor.evidence_refs", required=True)
        ensure_no_live_or_sensitive_text(self.summary, "LongTermAffectiveDriftMonitor.summary")
        if not self.report_only or self.mutates_core_policy:
            raise ValueError("affective drift monitor is report-only")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)
