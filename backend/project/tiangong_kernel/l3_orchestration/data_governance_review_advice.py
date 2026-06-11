"""L3 data governance review advice."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class DataGovernanceReviewRequestRef:
    request_ref: TypedRef
    subject_ref: TypedRef | None = None
    consent_ref: TypedRef | None = None
    purpose_ref: TypedRef | None = None
    retention_policy_ref: TypedRef | None = None
    trust_boundary_ref: TypedRef | None = None
    disclosure_boundary_ref: TypedRef | None = None
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class DataGovernanceAdvice:
    advice_ref: TypedRef
    review_request_ref: TypedRef | None = None
    missing_ref_names: tuple[str, ...] = field(default_factory=tuple)
    block_or_confirm_ref: TypedRef | None = None
    advisory_only: bool = True
    validates_consent: bool = False
    redacts_content: bool = False
    writes_memory: bool = False
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION


ConsentGapAdvice = DataGovernanceAdvice
ExternalDisclosureAdvice = DataGovernanceAdvice
CredentialUseAdvice = DataGovernanceAdvice
PrivacyInjectionAdvice = DataGovernanceAdvice
