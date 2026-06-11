"""Declarative capability-token requirements for L5 phase 2.

No real token is issued, refreshed, validated, or revoked here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version
from .phase2_common import ensure_no_plain_credential_values


@dataclass(frozen=True, slots=True)
class PluginCapabilityTokenDeclaration:
    required_token_refs: tuple[str, ...] = field(default_factory=tuple)
    token_scope_refs: tuple[str, ...] = field(default_factory=tuple)
    lease_ref: str = ""
    expires_at_ref: str = ""
    expiry_ref: str = ""
    revocation_check_ref: str = ""
    delegation_policy_ref: str = ""
    audience_ref: str = ""
    issuer_ref: str = ""
    subject_ref: str = ""
    token_issued: bool = False
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_items(self.required_token_refs, "PluginCapabilityTokenDeclaration.required_token_refs")
        ensure_ref_items(self.token_scope_refs, "PluginCapabilityTokenDeclaration.token_scope_refs")
        for name in (
            "lease_ref",
            "expires_at_ref",
            "expiry_ref",
            "revocation_check_ref",
            "delegation_policy_ref",
            "audience_ref",
            "issuer_ref",
            "subject_ref",
        ):
            ensure_ref_text(getattr(self, name), f"PluginCapabilityTokenDeclaration.{name}", required=False)
        if self.token_issued:
            raise ValueError("PluginCapabilityTokenDeclaration must not issue capability tokens")
        ensure_no_plain_credential_values(self, "PluginCapabilityTokenDeclaration")
        ensure_schema_version(self.schema_version, "PluginCapabilityTokenDeclaration.schema_version")
