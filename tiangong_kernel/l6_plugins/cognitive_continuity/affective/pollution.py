"""Affective pollution defense projections for L6 phase4."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l6_plugins.common._common import ensure_bool, ensure_score, ensure_ref_items
from ..projection import CognitiveOutputBase


def _score(value: float, field_name: str) -> None:
    ensure_score(value, field_name)


@dataclass(frozen=True)
class AffectivePollutionRiskProjection(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_affective_pollution_risk"
    plugin_ref: str = "l6_phase4:affective_reentry"
    pollution_risk_score: float = 0.0
    quarantine_hint_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase4_quarantine_hint",))
    demotion_hint_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase4_demotion_hint",))
    recovery_hint_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase4_recovery_hint",))
    removal_command: bool = False
    value_dictatorship: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.pollution_risk_score, "AffectivePollutionRiskProjection.pollution_risk_score")
        ensure_ref_items(self.quarantine_hint_refs, "AffectivePollutionRiskProjection.quarantine_hint_refs", required=True)
        ensure_ref_items(self.demotion_hint_refs, "AffectivePollutionRiskProjection.demotion_hint_refs", required=True)
        ensure_ref_items(self.recovery_hint_refs, "AffectivePollutionRiskProjection.recovery_hint_refs", required=True)
        ensure_bool(self.removal_command, "AffectivePollutionRiskProjection.removal_command")
        ensure_bool(self.value_dictatorship, "AffectivePollutionRiskProjection.value_dictatorship")
        if self.removal_command or self.value_dictatorship:
            raise ValueError("affective pollution risk is hint-only and not a deletion or value dictatorship")


@dataclass(frozen=True)
class ValueStabilityAnchorProjection(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_value_stability_anchor"
    plugin_ref: str = "l6_phase4:affective_reentry"
    anchor_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase4_positive_value_anchor",))
    substitutes_safety_policy: bool = False
    value_decision_engine: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.anchor_refs, "ValueStabilityAnchorProjection.anchor_refs", required=True)
        ensure_bool(self.substitutes_safety_policy, "ValueStabilityAnchorProjection.substitutes_safety_policy")
        ensure_bool(self.value_decision_engine, "ValueStabilityAnchorProjection.value_decision_engine")
        if self.substitutes_safety_policy or self.value_decision_engine:
            raise ValueError("value stability anchor cannot become policy or value decision engine")
