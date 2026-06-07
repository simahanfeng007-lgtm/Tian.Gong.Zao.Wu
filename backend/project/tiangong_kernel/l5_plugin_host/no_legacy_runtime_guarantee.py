"""L5 phase 1 guarantee that legacy main-chain execution is not restored."""

from __future__ import annotations

from dataclasses import dataclass

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_schema_version, ensure_short_text


@dataclass(frozen=True, slots=True)
class L5NoLegacyRuntimeGuarantee:
    guarantee_ref: str
    legacy_main_chain_present: bool = False
    legacy_capability_chain_present: bool = False
    summary: str = "L5 phase 1 exposes no legacy main-chain executor."
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.legacy_main_chain_present or self.legacy_capability_chain_present:
            raise ValueError("L5 phase 1 must not restore the legacy main chain")
        ensure_short_text(self.guarantee_ref, "L5NoLegacyRuntimeGuarantee.guarantee_ref", 128)
        ensure_short_text(self.summary, "L5NoLegacyRuntimeGuarantee.summary")
        ensure_schema_version(self.schema_version, "L5NoLegacyRuntimeGuarantee.schema_version")
