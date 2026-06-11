"""Declarative data governance, consent, purpose, and lifecycle boundaries."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version
from .phase2_common import ensure_no_plain_credential_values


@dataclass(frozen=True, slots=True)
class PluginDataGovernanceDeclaration:
    data_classification_refs: tuple[str, ...] = field(default_factory=tuple)
    privacy_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    retention_policy_ref: str = ""
    external_disclosure_policy_ref: str = ""
    taint_policy_ref: str = ""
    consent_refs: tuple[str, ...] = field(default_factory=tuple)
    purpose_refs: tuple[str, ...] = field(default_factory=tuple)
    data_lifecycle_refs: tuple[str, ...] = field(default_factory=tuple)
    data_subject_refs: tuple[str, ...] = field(default_factory=tuple)
    processing_basis_refs: tuple[str, ...] = field(default_factory=tuple)
    cross_boundary_transfer_refs: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "data_classification_refs",
            "privacy_boundary_refs",
            "consent_refs",
            "purpose_refs",
            "data_lifecycle_refs",
            "data_subject_refs",
            "processing_basis_refs",
            "cross_boundary_transfer_refs",
        ):
            ensure_ref_items(getattr(self, name), f"PluginDataGovernanceDeclaration.{name}")
        for name in ("retention_policy_ref", "external_disclosure_policy_ref", "taint_policy_ref"):
            ensure_ref_text(getattr(self, name), f"PluginDataGovernanceDeclaration.{name}", required=False)
        ensure_no_plain_credential_values(self, "PluginDataGovernanceDeclaration")
        ensure_schema_version(self.schema_version, "PluginDataGovernanceDeclaration.schema_version")
