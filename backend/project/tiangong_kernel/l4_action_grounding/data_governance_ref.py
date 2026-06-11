"""Data governance and privacy refs carried by L4 action envelopes."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class DataGovernanceRefBundle:
    bundle_ref: TypedRef
    data_governance_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    privacy_boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    consent_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    purpose_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    retention_policy_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    data_lifecycle_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    disclosure_boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    trust_boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    capability_token_ref: TypedRef | None = None
    revocation_ref: TypedRef | None = None
    credential_status_ref: TypedRef | None = None
    ref_only: bool = True
    contains_plain_secret: bool = False
    l4_validates_consent: bool = False
    l4_resolves_credential: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.ref_only, "DataGovernanceRefBundle.ref_only")
        ensure_false(self.contains_plain_secret, "DataGovernanceRefBundle.contains_plain_secret")
        ensure_false(self.l4_validates_consent, "DataGovernanceRefBundle.l4_validates_consent")
        ensure_false(self.l4_resolves_credential, "DataGovernanceRefBundle.l4_resolves_credential")
        ensure_schema_version(self.schema_version, "DataGovernanceRefBundle.schema_version")

    @property
    def has_privacy_governance_refs(self) -> bool:
        return bool(self.privacy_boundary_refs and self.consent_refs and self.purpose_refs and self.retention_policy_refs)


@dataclass(frozen=True, slots=True)
class CredentialRevocationSignalRef:
    signal_ref: TypedRef
    capability_token_ref: TypedRef | None = None
    credential_handle_ref: TypedRef | None = None
    revocation_ref: TypedRef | None = None
    explicit_revoked: bool = False
    ref_only: bool = True
    l4_revokes_token: bool = False
    l4_rotates_credential: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.ref_only, "CredentialRevocationSignalRef.ref_only")
        ensure_false(self.l4_revokes_token, "CredentialRevocationSignalRef.l4_revokes_token")
        ensure_false(self.l4_rotates_credential, "CredentialRevocationSignalRef.l4_rotates_credential")
        ensure_schema_version(self.schema_version, "CredentialRevocationSignalRef.schema_version")
