"""Credential boundary declarations for L6 phase5 governance-control."""

from __future__ import annotations

from dataclasses import dataclass

from .common import GovernanceArtifactBase, ensure_bool, ensure_ref_text, ensure_score


@dataclass(frozen=True)
class CredentialRequirementRef(GovernanceArtifactBase):
    object_ref: str = "credential-policy:l6_phase5_requirement_ref"
    requirement_ref: str = "credential-policy:l6_phase5_scoped_requirement"
    secret_access_granted: bool = False
    material_loaded: bool = False
    l5_credential_review_required: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.requirement_ref, "CredentialRequirementRef.requirement_ref")
        for field_name in ("secret_access_granted", "material_loaded", "l5_credential_review_required"):
            ensure_bool(getattr(self, field_name), f"CredentialRequirementRef.{field_name}")
        if self.secret_access_granted or self.material_loaded or not self.l5_credential_review_required:
            raise ValueError("CredentialRequirementRef is not credential access")


@dataclass(frozen=True)
class CredentialScopeHint(GovernanceArtifactBase):
    object_ref: str = "hint:l6_phase5_credential_scope"
    scope_ref: str = "credential-policy:l6_phase5_scope_summary"
    contains_locator: bool = False
    contains_secret_material: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.scope_ref, "CredentialScopeHint.scope_ref")
        ensure_bool(self.contains_locator, "CredentialScopeHint.contains_locator")
        ensure_bool(self.contains_secret_material, "CredentialScopeHint.contains_secret_material")
        if self.contains_locator or self.contains_secret_material:
            raise ValueError("Credential scope hint cannot contain locator or secret material")


@dataclass(frozen=True)
class CredentialRiskProjection(GovernanceArtifactBase):
    object_ref: str = "projection:l6_phase5_credential_risk"
    credential_risk_score: float = 0.5
    hard_boundary_review_required: bool = True
    reads_credentials: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_score(self.credential_risk_score, "CredentialRiskProjection.credential_risk_score")
        ensure_bool(self.hard_boundary_review_required, "CredentialRiskProjection.hard_boundary_review_required")
        ensure_bool(self.reads_credentials, "CredentialRiskProjection.reads_credentials")
        if not self.hard_boundary_review_required or self.reads_credentials:
            raise ValueError("Credential risk must request review without reading credentials")


@dataclass(frozen=True)
class SecretBoundaryProjection(GovernanceArtifactBase):
    object_ref: str = "projection:l6_phase5_secret_boundary"
    plain_material_allowed: bool = False
    locator_detail_allowed: bool = False
    redaction_required: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("plain_material_allowed", "locator_detail_allowed", "redaction_required"):
            ensure_bool(getattr(self, field_name), f"SecretBoundaryProjection.{field_name}")
        if self.plain_material_allowed or self.locator_detail_allowed or not self.redaction_required:
            raise ValueError("Secret boundary projection must block plain material and locator detail")


@dataclass(frozen=True)
class NoPlainSecretRequirement(GovernanceArtifactBase):
    object_ref: str = "credential-policy:l6_phase5_no_plain_secret"
    no_plain_material_required: bool = True
    no_provider_locator_required: bool = True
    accesses_secret_store: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("no_plain_material_required", "no_provider_locator_required", "accesses_secret_store"):
            ensure_bool(getattr(self, field_name), f"NoPlainSecretRequirement.{field_name}")
        if not self.no_plain_material_required or not self.no_provider_locator_required or self.accesses_secret_store:
            raise ValueError("NoPlainSecretRequirement must remain a requirement and not access store")


@dataclass(frozen=True)
class ProviderLocatorLeakRisk(GovernanceArtifactBase):
    object_ref: str = "projection:l6_phase5_provider_locator_leak_risk"
    locator_detail_present: bool = False
    raw_provider_locator_present: bool = False
    block_public_projection: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("locator_detail_present", "raw_provider_locator_present", "block_public_projection"):
            ensure_bool(getattr(self, field_name), f"ProviderLocatorLeakRisk.{field_name}")
        if self.locator_detail_present or self.raw_provider_locator_present or not self.block_public_projection:
            raise ValueError("Provider locator detail must not be present in L6 phase5 outputs")
