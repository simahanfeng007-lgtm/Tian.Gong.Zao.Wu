"""Declarative credential-handle requirements for L5 phase 2 manifests."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_bool, ensure_ref_items, ensure_ref_text, ensure_schema_version
from .phase2_common import ensure_no_plain_credential_values


@dataclass(frozen=True, slots=True)
class PluginCredentialDeclaration:
    credential_handle_refs: tuple[str, ...] = field(default_factory=tuple)
    secret_scope_refs: tuple[str, ...] = field(default_factory=tuple)
    redaction_required: bool = True
    rotation_policy_ref: str = ""
    credential_binding_refs: tuple[str, ...] = field(default_factory=tuple)
    credential_purpose_refs: tuple[str, ...] = field(default_factory=tuple)
    credential_audience_refs: tuple[str, ...] = field(default_factory=tuple)
    credential_revocation_ref: str = ""
    credential_lease_ref: str = ""
    value_absent_required: bool = True
    redacted_required: bool = True
    credential_values_absent: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_items(self.credential_handle_refs, "PluginCredentialDeclaration.credential_handle_refs")
        ensure_ref_items(self.secret_scope_refs, "PluginCredentialDeclaration.secret_scope_refs")
        ensure_bool(self.redaction_required, "PluginCredentialDeclaration.redaction_required")
        ensure_ref_text(self.rotation_policy_ref, "PluginCredentialDeclaration.rotation_policy_ref", required=False)
        ensure_ref_items(self.credential_binding_refs, "PluginCredentialDeclaration.credential_binding_refs")
        ensure_ref_items(self.credential_purpose_refs, "PluginCredentialDeclaration.credential_purpose_refs")
        ensure_ref_items(self.credential_audience_refs, "PluginCredentialDeclaration.credential_audience_refs")
        ensure_ref_text(self.credential_revocation_ref, "PluginCredentialDeclaration.credential_revocation_ref", required=False)
        ensure_ref_text(self.credential_lease_ref, "PluginCredentialDeclaration.credential_lease_ref", required=False)
        ensure_bool(self.value_absent_required, "PluginCredentialDeclaration.value_absent_required")
        ensure_bool(self.redacted_required, "PluginCredentialDeclaration.redacted_required")
        ensure_ref_items(self.credential_values_absent, "PluginCredentialDeclaration.credential_values_absent")
        if not self.value_absent_required or not self.redacted_required:
            raise ValueError("PluginCredentialDeclaration must require absent and redacted credential values")
        ensure_no_plain_credential_values(self, "PluginCredentialDeclaration")
        ensure_schema_version(self.schema_version, "PluginCredentialDeclaration.schema_version")
