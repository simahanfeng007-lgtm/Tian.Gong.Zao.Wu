"""L6 phase4 product-production bridge seed contracts.

Phase4 is not a product-production stage.  These objects only preserve future
bridge references for later stages.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l6_plugins.common._common import ensure_bool, ensure_ref_items, ensure_ref_text
from .common import CognitiveOutputKind
from .projection import CognitiveOutputBase


@dataclass(frozen=True)
class ProductContextSafetyProjection(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_product_context_safety"
    plugin_ref: str = "l6_phase4:product_bridge_seed"
    product_seed_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_product_spec_seed_candidate",))
    privacy_classification_ref: str = "policy:l6_phase4_product_privacy_classification"
    artifact_context_risk_ref: str = "projection:l6_phase4_product_artifact_context_risk"
    raw_input_redaction_ref: str = "redaction:l6_phase4_product_raw_input"
    build_context_created: bool = False
    product_spec_context_created: bool = False
    raw_task_context_exposed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__(); ensure_ref_items(self.product_seed_refs, "ProductContextSafetyProjection.product_seed_refs", required=True)
        for field_name in ("privacy_classification_ref", "artifact_context_risk_ref", "raw_input_redaction_ref"):
            ensure_ref_text(getattr(self, field_name), f"ProductContextSafetyProjection.{field_name}")
        ensure_bool(self.build_context_created, "ProductContextSafetyProjection.build_context_created")
        ensure_bool(self.product_spec_context_created, "ProductContextSafetyProjection.product_spec_context_created")
        ensure_bool(self.raw_task_context_exposed, "ProductContextSafetyProjection.raw_task_context_exposed")
        if self.build_context_created or self.product_spec_context_created or self.raw_task_context_exposed:
            raise ValueError("product context safety projection cannot create build/ProductSpec context or expose raw context")


@dataclass(frozen=True)
class ProductBridgeReentryEnvelope(CognitiveOutputBase):
    output_ref: str = "l6:l6_phase4_product_bridge_reentry_envelope"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.REENTRY_ENVELOPE
    plugin_ref: str = "l6_phase4:product_bridge_seed"
    seed_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_product_spec_seed_candidate",))
    l3_l5_review_required: bool = True
    build_action_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__(); ensure_ref_items(self.seed_refs, "ProductBridgeReentryEnvelope.seed_refs", required=True)
        ensure_bool(self.l3_l5_review_required, "ProductBridgeReentryEnvelope.l3_l5_review_required")
        ensure_bool(self.build_action_allowed, "ProductBridgeReentryEnvelope.build_action_allowed")
        if not self.l3_l5_review_required or self.build_action_allowed:
            raise ValueError("product bridge reentry is future review-only bridge")
