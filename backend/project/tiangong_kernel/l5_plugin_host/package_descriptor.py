"""L5 plugin package descriptor shell.

Phase 2 enhances the descriptor with manifest declaration references. It still
stores only logical refs and in-memory declaration objects; it never scans real
plugin directories, reads package files, validates filesystem existence, or
writes a plugin registry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, digest_without, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text
from .audit_declaration import PluginAuditDeclaration
from .capability_token_declaration import PluginCapabilityTokenDeclaration
from .compatibility_declaration import PluginCompatibilityDeclaration
from .credential_declaration import PluginCredentialDeclaration
from .data_governance_declaration import PluginDataGovernanceDeclaration
from .entry_reference import PluginEntryReference
from .hot_switch_declaration import PluginHotSwitchDeclaration
from .manifest_hash import PluginManifestHash
from .mount_surface_declaration import PluginMountSurfaceDeclaration
from .permission_declaration import PluginPermissionDeclaration
from .resource_declaration import PluginResourceDeclaration
from .rollback_declaration import PluginRollbackDeclaration
from .signature_reference import PluginSignatureReference
from .source_trust import PluginSourceTrustReference
from .trust_boundary_declaration import PluginTrustBoundaryDeclaration
from .version_declaration import PluginVersionDeclaration


@dataclass(frozen=True, slots=True)
class PluginPackageDescriptor:
    package_ref: str
    manifest_ref: str
    source_summary: str = ""
    source_digest: str = ""
    actor_ref: str = ""
    scope_ref: str = ""
    trace_ref: str = ""
    policy_ref: str = ""
    approval_ref: str = ""
    handoff_ref: str = ""
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    accountability_ref: str = ""
    tamper_evidence_ref: str = ""
    validation_requirement_refs: tuple[str, ...] = field(default_factory=tuple)
    verification_requirement_refs: tuple[str, ...] = field(default_factory=tuple)
    package_digest: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION
    entry_ref: Any = None
    mount_surfaces: tuple[PluginMountSurfaceDeclaration, ...] = field(default_factory=tuple)
    permission_decl: Any = None
    resource_decl: Any = None
    credential_decl: Any = None
    data_governance_decl: Any = None
    audit_decl: Any = None
    version_decl: Any = None
    rollback_decl: Any = None
    compatibility_decl: Any = None
    capability_token_decl: Any = None
    trust_boundary_decl: Any = None
    source_trust_ref: Any = None
    signature_ref: Any = None
    manifest_hash: Any = None
    hot_switch_decl: Any = None

    def __post_init__(self) -> None:
        ensure_ref_text(self.package_ref, "PluginPackageDescriptor.package_ref")
        ensure_ref_text(self.manifest_ref, "PluginPackageDescriptor.manifest_ref")
        ensure_short_text(self.source_summary, "PluginPackageDescriptor.source_summary")
        ensure_ref_text(self.source_digest, "PluginPackageDescriptor.source_digest", required=False)
        for attr in ("actor_ref", "scope_ref", "trace_ref", "policy_ref", "approval_ref", "handoff_ref", "accountability_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, attr), f"PluginPackageDescriptor.{attr}", required=False)
        ensure_ref_items(self.evidence_refs, "PluginPackageDescriptor.evidence_refs")
        ensure_ref_items(self.provenance_refs, "PluginPackageDescriptor.provenance_refs")
        ensure_ref_items(self.validation_requirement_refs, "PluginPackageDescriptor.validation_requirement_refs")
        ensure_ref_items(self.verification_requirement_refs, "PluginPackageDescriptor.verification_requirement_refs")
        ensure_schema_version(self.schema_version, "PluginPackageDescriptor.schema_version")
        for surface in self.mount_surfaces:
            if not isinstance(surface, PluginMountSurfaceDeclaration):
                raise ValueError("PluginPackageDescriptor.mount_surfaces must contain PluginMountSurfaceDeclaration")
        for attr, expected in (
            ("entry_ref", PluginEntryReference),
            ("permission_decl", PluginPermissionDeclaration),
            ("resource_decl", PluginResourceDeclaration),
            ("credential_decl", PluginCredentialDeclaration),
            ("data_governance_decl", PluginDataGovernanceDeclaration),
            ("audit_decl", PluginAuditDeclaration),
            ("version_decl", PluginVersionDeclaration),
            ("rollback_decl", PluginRollbackDeclaration),
            ("compatibility_decl", PluginCompatibilityDeclaration),
            ("capability_token_decl", PluginCapabilityTokenDeclaration),
            ("trust_boundary_decl", PluginTrustBoundaryDeclaration),
            ("source_trust_ref", PluginSourceTrustReference),
            ("signature_ref", PluginSignatureReference),
            ("manifest_hash", PluginManifestHash),
            ("hot_switch_decl", PluginHotSwitchDeclaration),
        ):
            value = getattr(self, attr)
            if value is not None and not isinstance(value, expected):
                raise ValueError(f"PluginPackageDescriptor.{attr} must be {expected.__name__}")
        if self.package_digest:
            ensure_ref_text(self.package_digest, "PluginPackageDescriptor.package_digest")
        else:
            object.__setattr__(self, "package_digest", digest_without(self, ("package_digest",)))
