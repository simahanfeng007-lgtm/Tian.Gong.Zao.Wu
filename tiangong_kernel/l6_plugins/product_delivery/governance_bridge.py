"""Bridge from product-delivery candidates into phase5 governance review."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l6_plugins.governance_control.governance_review import GovernanceReviewRequest
from .common import ProductArtifactBase, ensure_bool, ensure_ref_items, ensure_ref_text


@dataclass(frozen=True)
class ProductGovernanceReviewRequest(ProductArtifactBase):
    object_ref: str = "request:l6_phase6_product_governance_review"
    review_target_refs: tuple[str, ...] = field(default_factory=lambda: ("product:l6_phase6_candidate",))
    phase5_review_required: bool = True
    issues_final_governance: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.review_target_refs, "ProductGovernanceReviewRequest.review_target_refs", required=True)
        ensure_bool(self.phase5_review_required, "ProductGovernanceReviewRequest.phase5_review_required")
        ensure_bool(self.issues_final_governance, "ProductGovernanceReviewRequest.issues_final_governance")
        if not self.phase5_review_required or self.issues_final_governance:
            raise ValueError("ProductGovernanceReviewRequest must defer final governance to phase5/L5")

    def to_phase5_request(self) -> GovernanceReviewRequest:
        return GovernanceReviewRequest(
            object_ref="request:l6_phase6_to_phase5_governance_review",
            risk_projection_refs=("projection:l6_phase6_product_risk",),
            permission_requirement_refs=("permission:l6_phase6_product_permission_requirement",),
            budget_requirement_refs=("budget:l6_phase6_product_budget_requirement",),
            audit_requirement_refs=("audit:l6_phase6_product_audit_requirement",),
            credential_requirement_refs=("credential-policy:l6_phase6_product_credential_requirement",),
            privacy_requirement_refs=("requirement:l6_phase6_product_privacy_requirement",),
        )


@dataclass(frozen=True)
class ProductPermissionRequirement(ProductArtifactBase):
    object_ref: str = "permission:l6_phase6_product_permission_requirement"
    permission_scope_refs: tuple[str, ...] = field(default_factory=lambda: ("policy:l6_phase6_permission_scope",))
    grants_permission: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.permission_scope_refs, "ProductPermissionRequirement.permission_scope_refs", required=True)
        ensure_bool(self.grants_permission, "ProductPermissionRequirement.grants_permission")
        if self.grants_permission:
            raise ValueError("ProductPermissionRequirement cannot grant permission")


@dataclass(frozen=True)
class ProductBudgetRequirement(ProductArtifactBase):
    object_ref: str = "budget:l6_phase6_product_budget_requirement"
    budget_scope_refs: tuple[str, ...] = field(default_factory=lambda: ("budget:l6_phase6_product_scope",))
    allocates_budget: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.budget_scope_refs, "ProductBudgetRequirement.budget_scope_refs", required=True)
        ensure_bool(self.allocates_budget, "ProductBudgetRequirement.allocates_budget")
        if self.allocates_budget:
            raise ValueError("ProductBudgetRequirement cannot allocate or charge budget")


@dataclass(frozen=True)
class ProductAuditRequirement(ProductArtifactBase):
    object_ref: str = "audit:l6_phase6_product_audit_requirement"
    audit_scope_refs: tuple[str, ...] = field(default_factory=lambda: ("audit:l6_phase6_product_scope",))
    writes_audit_store: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.audit_scope_refs, "ProductAuditRequirement.audit_scope_refs", required=True)
        ensure_bool(self.writes_audit_store, "ProductAuditRequirement.writes_audit_store")
        if self.writes_audit_store:
            raise ValueError("ProductAuditRequirement cannot write audit store")


@dataclass(frozen=True)
class ProductCredentialRequirementRef(ProductArtifactBase):
    object_ref: str = "credential-policy:l6_phase6_product_credential_requirement"
    credential_scope_ref: str = "credential-policy:l6_phase6_scope_ref_only"
    reads_credential_material: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.credential_scope_ref, "ProductCredentialRequirementRef.credential_scope_ref")
        ensure_bool(self.reads_credential_material, "ProductCredentialRequirementRef.reads_credential_material")
        if self.reads_credential_material:
            raise ValueError("ProductCredentialRequirementRef is not credential access")


@dataclass(frozen=True)
class ProductPrivacyRequirement(ProductArtifactBase):
    object_ref: str = "requirement:l6_phase6_product_privacy_requirement"
    redaction_refs: tuple[str, ...] = field(default_factory=lambda: ("redaction:l6_phase6_minimal_disclosure",))
    reads_full_private_content: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.redaction_refs, "ProductPrivacyRequirement.redaction_refs", required=True)
        ensure_bool(self.reads_full_private_content, "ProductPrivacyRequirement.reads_full_private_content")
        if self.reads_full_private_content:
            raise ValueError("ProductPrivacyRequirement cannot read full private content")


@dataclass(frozen=True)
class ProductHumanGateRequirement(ProductArtifactBase):
    object_ref: str = "requirement:l6_phase6_product_human_gate"
    reason_ref: str = "review:l6_phase6_human_gate_reason"
    confirmation_ticket_issued: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.reason_ref, "ProductHumanGateRequirement.reason_ref")
        ensure_bool(self.confirmation_ticket_issued, "ProductHumanGateRequirement.confirmation_ticket_issued")
        if self.confirmation_ticket_issued:
            raise ValueError("ProductHumanGateRequirement cannot issue confirmation tickets")


@dataclass(frozen=True)
class ProductDegradationSuggestion(ProductArtifactBase):
    object_ref: str = "suggestion:l6_phase6_product_degradation"
    degradation_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_degrade_to_structure_or_manual_steps",))
    aborts_task: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.degradation_refs, "ProductDegradationSuggestion.degradation_refs", required=True)
        ensure_bool(self.aborts_task, "ProductDegradationSuggestion.aborts_task")
        if self.aborts_task:
            raise ValueError("ProductDegradationSuggestion should degrade/continue, not abort")
