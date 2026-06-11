"""L5 plugin registry snapshot shells.

Phase 1 exposed an immutable entry snapshot. Phase 3 extends the same safe
object with declaration-only registry records, deterministic canonical digest,
revision references, and delta baseline references. It remains non-persistent
and cannot register, enable, disable, load, mount, isolate, or roll back plugins.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, digest_without, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text
from .registry_entry import PluginRegistryEntry
from .registry_record import PluginRegistryRecord
from .registry_serialization import registry_canonical_digest, registry_sort_key


@dataclass(frozen=True, slots=True)
class PluginRegistrySnapshot:
    snapshot_ref: str
    entries: tuple[PluginRegistryEntry, ...] = field(default_factory=tuple)
    records: tuple[PluginRegistryRecord, ...] = field(default_factory=tuple)
    revision_ref: str = ""
    base_snapshot_ref: str = ""
    delta_baseline_ref: str = ""
    actor_ref: str = ""
    scope_ref: str = ""
    trace_ref: str = ""
    policy_ref: str = ""
    approval_ref: str = ""
    handoff_ref: str = ""
    responsibility_chain_ref: str = ""
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    accountability_ref: str = ""
    tamper_evidence_ref: str = ""
    summary: str = ""
    registry_snapshot_digest: str = ""
    snapshot_digest: str = ""
    registry_digest: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.snapshot_ref, "PluginRegistrySnapshot.snapshot_ref")
        for item in self.entries:
            if not isinstance(item, PluginRegistryEntry):
                raise ValueError("PluginRegistrySnapshot.entries must contain PluginRegistryEntry")
        for item in self.records:
            if not isinstance(item, PluginRegistryRecord):
                raise ValueError("PluginRegistrySnapshot.records must contain PluginRegistryRecord")
        for name in (
            "revision_ref", "base_snapshot_ref", "delta_baseline_ref", "actor_ref", "scope_ref", "trace_ref",
            "policy_ref", "approval_ref", "handoff_ref", "responsibility_chain_ref", "accountability_ref",
            "tamper_evidence_ref",
        ):
            ensure_ref_text(getattr(self, name), f"PluginRegistrySnapshot.{name}", required=False)
        ensure_ref_items(self.evidence_refs, "PluginRegistrySnapshot.evidence_refs")
        ensure_ref_items(self.provenance_refs, "PluginRegistrySnapshot.provenance_refs")
        ensure_short_text(self.summary, "PluginRegistrySnapshot.summary")
        ensure_schema_version(self.schema_version, "PluginRegistrySnapshot.schema_version")
        ordered_records = tuple(sorted(self.records, key=registry_sort_key))
        if ordered_records != self.records:
            object.__setattr__(self, "records", ordered_records)
        digest_value = self.snapshot_digest or self.registry_snapshot_digest or registry_canonical_digest(self)
        if self.registry_snapshot_digest:
            ensure_ref_text(self.registry_snapshot_digest, "PluginRegistrySnapshot.registry_snapshot_digest")
        if self.snapshot_digest:
            ensure_ref_text(self.snapshot_digest, "PluginRegistrySnapshot.snapshot_digest")
        if self.registry_digest:
            ensure_ref_text(self.registry_digest, "PluginRegistrySnapshot.registry_digest")
        if not self.registry_snapshot_digest:
            object.__setattr__(self, "registry_snapshot_digest", digest_value)
        if not self.snapshot_digest:
            object.__setattr__(self, "snapshot_digest", digest_value)
        if not self.registry_digest:
            object.__setattr__(self, "registry_digest", digest_value)
