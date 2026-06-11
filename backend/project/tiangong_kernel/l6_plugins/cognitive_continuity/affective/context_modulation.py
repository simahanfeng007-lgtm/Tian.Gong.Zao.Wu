"""Affective context modulation hints for L6 phase4."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l6_plugins.common._common import ensure_bool, ensure_score, ensure_ref_items
from ..projection import CognitiveOutputBase


def _score(value: float, field_name: str) -> None:
    ensure_score(value, field_name)


@dataclass(frozen=True)
class AffectiveContextModulationHint(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_affective_context_modulation"
    plugin_ref: str = "l6_phase4:affective_reentry"
    attention_sensitivity_delta: float = 0.0
    compression_hint_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase4_context_compression_hint",))
    pollution_risk_hint_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase4_context_pollution_hint",))
    is_context_injection: bool = False
    bypasses_context_policy: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(abs(self.attention_sensitivity_delta), "AffectiveContextModulationHint.attention_sensitivity_delta_abs")
        ensure_ref_items(self.compression_hint_refs, "AffectiveContextModulationHint.compression_hint_refs", required=True)
        ensure_ref_items(self.pollution_risk_hint_refs, "AffectiveContextModulationHint.pollution_risk_hint_refs", required=True)
        ensure_bool(self.is_context_injection, "AffectiveContextModulationHint.is_context_injection")
        ensure_bool(self.bypasses_context_policy, "AffectiveContextModulationHint.bypasses_context_policy")
        if self.is_context_injection or self.bypasses_context_policy:
            raise ValueError("affective context hint cannot inject context or bypass policy")
