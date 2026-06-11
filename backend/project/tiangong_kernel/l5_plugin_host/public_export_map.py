"""L5 phase 1 public export map shell."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_text, ensure_schema_version, ensure_text_items


@dataclass(frozen=True, slots=True)
class L5PublicExportMap:
    export_map_ref: str
    safe_exports: tuple[str, ...] = field(default_factory=tuple)
    blocked_exports: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.export_map_ref, "L5PublicExportMap.export_map_ref")
        ensure_text_items(self.safe_exports, "L5PublicExportMap.safe_exports", limit=128)
        ensure_text_items(self.blocked_exports, "L5PublicExportMap.blocked_exports", limit=128)
        ensure_schema_version(self.schema_version, "L5PublicExportMap.schema_version")
