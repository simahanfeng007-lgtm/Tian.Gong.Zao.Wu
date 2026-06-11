"""Signature references for L5 phase 2.

This stores signature reference metadata only. It does not read keys,
certificates, or execute signature verification.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text


@dataclass(frozen=True, slots=True)
class PluginSignatureReference:
    signature_ref: str
    digest_ref: str = ""
    algorithm_ref: str = ""
    signer_ref: str = ""
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    verified: bool = False
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.signature_ref, "PluginSignatureReference.signature_ref")
        ensure_ref_text(self.digest_ref, "PluginSignatureReference.digest_ref", required=False)
        ensure_short_text(self.algorithm_ref, "PluginSignatureReference.algorithm_ref", 128)
        ensure_ref_text(self.signer_ref, "PluginSignatureReference.signer_ref", required=False)
        ensure_ref_items(self.evidence_refs, "PluginSignatureReference.evidence_refs")
        if self.verified:
            raise ValueError("PluginSignatureReference must not perform real signature verification")
        ensure_schema_version(self.schema_version, "PluginSignatureReference.schema_version")
