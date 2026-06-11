"""Source trust references for L5 phase 2.

This stores trust references only. It does not query remote trust services or
resolve certificates.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_digest, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text


@dataclass(frozen=True, slots=True)
class PluginSourceTrustReference:
    trust_ref: str
    trust_kind: str = "declared_source_trust"
    trust_digest: str = ""
    source_layer: str = "L5.phase2"
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    verified: bool = False
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.trust_ref, "PluginSourceTrustReference.trust_ref")
        ensure_short_text(self.trust_kind, "PluginSourceTrustReference.trust_kind", 128)
        ensure_digest(self.trust_digest, "PluginSourceTrustReference.trust_digest")
        ensure_ref_text(self.source_layer, "PluginSourceTrustReference.source_layer")
        ensure_ref_items(self.evidence_refs, "PluginSourceTrustReference.evidence_refs")
        if self.verified:
            raise ValueError("PluginSourceTrustReference must not perform real trust verification")
        ensure_schema_version(self.schema_version, "PluginSourceTrustReference.schema_version")
