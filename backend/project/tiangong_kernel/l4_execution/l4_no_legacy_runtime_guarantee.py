"""No legacy main-chain guarantee for L4 phase 8 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import LEGACY_MAIN_CHAIN_SYMBOLS, L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_text_items, ensure_true


@dataclass(frozen=True, slots=True)
class L4NoLegacyRuntimeGuarantee:
    """Guarantee that L4 closure does not restore the legacy main chain."""

    guarantee_ref: TypedRef
    forbidden_symbols: tuple[str, ...] = field(default_factory=lambda: LEGACY_MAIN_CHAIN_SYMBOLS)
    guarantee_only: bool = True
    restores_legacy_main_chain: bool = False
    restores_ability_package: bool = False
    restores_capability_port: bool = False
    creates_old_router: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_text_items(self.forbidden_symbols, "L4NoLegacyRuntimeGuarantee.forbidden_symbols", 128)
        ensure_true(self.guarantee_only, "L4NoLegacyRuntimeGuarantee.guarantee_only")
        ensure_false(self.restores_legacy_main_chain, "L4NoLegacyRuntimeGuarantee.restores_legacy_main_chain")
        ensure_false(self.restores_ability_package, "L4NoLegacyRuntimeGuarantee.restores_ability_package")
        ensure_false(self.restores_capability_port, "L4NoLegacyRuntimeGuarantee.restores_capability_port")
        ensure_false(self.creates_old_router, "L4NoLegacyRuntimeGuarantee.creates_old_router")
        ensure_schema_version(self.schema_version, "L4NoLegacyRuntimeGuarantee.schema_version")
