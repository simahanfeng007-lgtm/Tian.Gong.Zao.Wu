"""Affective memory modulation hints for L6 phase4."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l6_plugins.common._common import ensure_bool, ensure_score
from ..projection import CognitiveOutputBase


def _score(value: float, field_name: str) -> None:
    ensure_score(value, field_name)


@dataclass(frozen=True)
class AffectiveMemoryWeightHint(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_affective_memory_weight_hint"
    plugin_ref: str = "l6_phase4:affective_reentry"
    salience_delta: float = 0.0
    user_feedback_intensity: float = 0.0
    emotional_relevance: float = 0.0
    is_memory_update_proposal: bool = False
    force_recall: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("salience_delta", "user_feedback_intensity", "emotional_relevance"):
            _score(abs(getattr(self, field_name)), f"AffectiveMemoryWeightHint.{field_name}_abs")
        ensure_bool(self.is_memory_update_proposal, "AffectiveMemoryWeightHint.is_memory_update_proposal")
        ensure_bool(self.force_recall, "AffectiveMemoryWeightHint.force_recall")
        if self.is_memory_update_proposal or self.force_recall:
            raise ValueError("affective memory weight hint cannot write or force memory")
