"""L5 phase 1 guarantee that no L6 business plugin is implemented here."""

from __future__ import annotations

from dataclasses import dataclass

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_schema_version, ensure_short_text


@dataclass(frozen=True, slots=True)
class L5NoL6ImplementationGuarantee:
    guarantee_ref: str
    l6_business_logic_present: bool = False
    business_plugin_methods_present: bool = False
    summary: str = "L5 phase 1 contains data-only host shells."
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.l6_business_logic_present or self.business_plugin_methods_present:
            raise ValueError("L5 phase 1 must not contain L6 business plugin logic")
        ensure_short_text(self.guarantee_ref, "L5NoL6ImplementationGuarantee.guarantee_ref", 128)
        ensure_short_text(self.summary, "L5NoL6ImplementationGuarantee.summary")
        ensure_schema_version(self.schema_version, "L5NoL6ImplementationGuarantee.schema_version")
