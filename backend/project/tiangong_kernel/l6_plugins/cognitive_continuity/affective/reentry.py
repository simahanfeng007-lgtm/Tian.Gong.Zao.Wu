"""Affective reentry envelope for L6 phase4."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l6_plugins.common._common import L6_COMMON_SCHEMA_VERSION, ensure_bool, ensure_ref_items, ensure_ref_text, ensure_schema_version, stable_digest


@dataclass(frozen=True)
class AffectiveReentryEnvelope:
    envelope_ref: str = "l6:l6_phase4_affective_reentry"
    affective_projection_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_affective_projection",))
    cognitive_reentry_ref: str = "l6:l6_phase4_cognitive_reentry_envelope"
    l3_review_required: bool = True
    l5_review_required: bool = True
    l2_direct_write: bool = False
    memory_direct_write: bool = False
    forgetting_direct_removal: bool = False
    model_direct_dispatch: bool = False
    tool_direct_dispatch: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.envelope_ref, "AffectiveReentryEnvelope.envelope_ref")
        ensure_ref_items(self.affective_projection_refs, "AffectiveReentryEnvelope.affective_projection_refs", required=True)
        ensure_ref_text(self.cognitive_reentry_ref, "AffectiveReentryEnvelope.cognitive_reentry_ref")
        for field_name in (
            "l3_review_required", "l5_review_required", "l2_direct_write", "memory_direct_write", "forgetting_direct_removal", "model_direct_dispatch", "tool_direct_dispatch",
        ):
            ensure_bool(getattr(self, field_name), f"AffectiveReentryEnvelope.{field_name}")
        if not self.l3_review_required or not self.l5_review_required:
            raise ValueError("affective reentry must go through L3/L5")
        if any((self.l2_direct_write, self.memory_direct_write, self.forgetting_direct_removal, self.model_direct_dispatch, self.tool_direct_dispatch)):
            raise ValueError("affective reentry cannot perform privileged actions")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)
