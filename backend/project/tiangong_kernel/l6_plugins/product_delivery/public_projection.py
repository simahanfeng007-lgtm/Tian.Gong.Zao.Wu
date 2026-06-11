"""Public projection candidates for L6 phase6 product delivery."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import ProductArtifactBase, ProductPrivacyClass, ProductRedactionState, ensure_bool, ensure_ref_items


@dataclass(frozen=True)
class ProductPublicProjection(ProductArtifactBase):
    object_ref: str = "public:l6_phase6_product_projection"
    redaction_state: ProductRedactionState | str = ProductRedactionState.APPLIED_SUMMARY_ONLY
    privacy_class: ProductPrivacyClass | str = ProductPrivacyClass.PUBLIC_SUMMARY
    exposes_full_prompt: bool = False
    exposes_full_context: bool = False
    exposes_private_memory: bool = False
    exposes_real_locator: bool = False
    exposes_executable_plan: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in (
            "exposes_full_prompt", "exposes_full_context", "exposes_private_memory", "exposes_real_locator", "exposes_executable_plan",
        ):
            ensure_bool(getattr(self, field_name), f"ProductPublicProjection.{field_name}")
        if any((self.exposes_full_prompt, self.exposes_full_context, self.exposes_private_memory, self.exposes_real_locator, self.exposes_executable_plan)):
            raise ValueError("ProductPublicProjection must keep minimal disclosure")


@dataclass(frozen=True)
class ProductDeliveryPublicSummary(ProductArtifactBase):
    object_ref: str = "public:l6_phase6_delivery_summary"
    summary_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_delivery_public",))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.summary_refs, "ProductDeliveryPublicSummary.summary_refs", required=True)


@dataclass(frozen=True)
class ProductRiskPublicSummary(ProductArtifactBase):
    object_ref: str = "public:l6_phase6_risk_summary"
    risk_level_ref: str = "summary:l6_phase6_risk_level"


@dataclass(frozen=True)
class ProductProgressPublicSummary(ProductArtifactBase):
    object_ref: str = "public:l6_phase6_progress_summary"
    progress_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_progress_public",))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.progress_refs, "ProductProgressPublicSummary.progress_refs", required=True)


@dataclass(frozen=True)
class ProductRedactionReport(ProductArtifactBase):
    object_ref: str = "redaction:l6_phase6_product_redaction_report"
    blocked_field_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_blocked_sensitive_detail",))
    minimal_disclosure_passed: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.blocked_field_refs, "ProductRedactionReport.blocked_field_refs", required=True)
        ensure_bool(self.minimal_disclosure_passed, "ProductRedactionReport.minimal_disclosure_passed")
        if not self.minimal_disclosure_passed:
            raise ValueError("ProductRedactionReport must pass minimal disclosure to be public")
