"""L5 phase 1 edit-scope and hash-manifest shells."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text, ensure_text_items


@dataclass(frozen=True, slots=True)
class L5Phase1EditablePathScope:
    scope_ref: str
    allowed_prefixes: tuple[str, ...] = field(default_factory=lambda: (
        "tiangong_kernel/l5_plugin_host/",
        "tests/test_l5_phase1_",
        "docs/l5_phase1_",
    ))
    exception_refs: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.scope_ref, "L5Phase1EditablePathScope.scope_ref")
        ensure_text_items(self.allowed_prefixes, "L5Phase1EditablePathScope.allowed_prefixes", limit=256)
        ensure_ref_items(self.exception_refs, "L5Phase1EditablePathScope.exception_refs")
        ensure_schema_version(self.schema_version, "L5Phase1EditablePathScope.schema_version")


@dataclass(frozen=True, slots=True)
class L5Phase1HashManifestRecord:
    record_ref: str
    path: str
    sha256: str
    layer: str
    summary: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.record_ref, "L5Phase1HashManifestRecord.record_ref")
        ensure_short_text(self.path, "L5Phase1HashManifestRecord.path", 512)
        ensure_ref_text(self.sha256, "L5Phase1HashManifestRecord.sha256")
        ensure_short_text(self.layer, "L5Phase1HashManifestRecord.layer", 64)
        ensure_short_text(self.summary, "L5Phase1HashManifestRecord.summary")
        ensure_schema_version(self.schema_version, "L5Phase1HashManifestRecord.schema_version")
