"""Affective public projection with minimal disclosure."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l6_plugins.common._common import ensure_bool, ensure_ref_items, ensure_ref_text
from ..projection import CognitiveOutputBase, PublicDisclosureClass


class AffectivePublicStatus(str, Enum):
    NORMAL = "normal"
    PRESSURED = "pressured"
    DEGRADED = "degraded"
    POLLUTION_RISK = "pollution_risk"


@dataclass(frozen=True)
class AffectivePublicProjection(CognitiveOutputBase):
    output_ref: str = "public:l6_phase4_affective_public_projection"
    plugin_ref: str = "l6_phase4:affective_reentry"
    disclosure_class: PublicDisclosureClass | str = PublicDisclosureClass.PUBLIC_MINIMAL
    status: AffectivePublicStatus | str = AffectivePublicStatus.NORMAL
    risk_level_ref: str = "summary:l6_phase4_affective_risk_low"
    governance_reason_present: bool = False
    suggests_degradation: bool = False
    evidence_count: int = 1
    redaction_flags: tuple[str, ...] = field(default_factory=lambda: (
        "redact:full_affective_profile", "redact:full_vector", "redact:raw_emotion_evidence", "redact:full_prompt", "redact:provider_locator", "redact:execution_plan"
    ))
    full_affective_profile_public: bool = False
    full_vector_public: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "status", AffectivePublicStatus(self.status))
        ensure_ref_text(self.risk_level_ref, "AffectivePublicProjection.risk_level_ref")
        ensure_bool(self.governance_reason_present, "AffectivePublicProjection.governance_reason_present")
        ensure_bool(self.suggests_degradation, "AffectivePublicProjection.suggests_degradation")
        if not isinstance(self.evidence_count, int) or self.evidence_count < 0:
            raise ValueError("AffectivePublicProjection.evidence_count must be non-negative integer")
        ensure_ref_items(self.redaction_flags, "AffectivePublicProjection.redaction_flags", required=True)
        ensure_bool(self.full_affective_profile_public, "AffectivePublicProjection.full_affective_profile_public")
        ensure_bool(self.full_vector_public, "AffectivePublicProjection.full_vector_public")
        if self.full_affective_profile_public or self.full_vector_public:
            raise ValueError("affective public projection must hide full profile and vectors")
