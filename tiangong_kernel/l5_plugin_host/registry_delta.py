"""L5 phase 3 registry delta declarations.

Deltas describe differences only. They are not patches and intentionally expose
no method that applies, commits, rolls back, mounts, enables, disables, isolates,
or hot-switches plugin records.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version
from .registry_key import PluginRegistryKey
from .registry_record import PluginRegistryRecord
from .registry_serialization import registry_canonical_digest
from .registry_snapshot import PluginRegistrySnapshot

DELTA_ITEM_ADDED = "added"
DELTA_ITEM_REMOVED = "removed"
DELTA_ITEM_CHANGED = "changed"
DELTA_ITEM_UNCHANGED = "unchanged"
_ALLOWED_ITEM_KINDS = (DELTA_ITEM_ADDED, DELTA_ITEM_REMOVED, DELTA_ITEM_CHANGED, DELTA_ITEM_UNCHANGED)


@dataclass(frozen=True, slots=True)
class PluginRegistryDeltaItem:
    item_kind: str
    registry_key: PluginRegistryKey
    base_record_digest: str = ""
    target_record_digest: str = ""
    changed_fields: tuple[str, ...] = field(default_factory=tuple)
    conflict_refs: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    item_digest: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.item_kind not in _ALLOWED_ITEM_KINDS:
            raise ValueError("PluginRegistryDeltaItem.item_kind has unsupported value")
        if not isinstance(self.registry_key, PluginRegistryKey):
            raise ValueError("PluginRegistryDeltaItem.registry_key must be PluginRegistryKey")
        ensure_ref_text(self.base_record_digest, "PluginRegistryDeltaItem.base_record_digest", required=False)
        ensure_ref_text(self.target_record_digest, "PluginRegistryDeltaItem.target_record_digest", required=False)
        for field_name in self.changed_fields:
            ensure_ref_text(field_name, "PluginRegistryDeltaItem.changed_fields")
        ensure_ref_items(self.conflict_refs, "PluginRegistryDeltaItem.conflict_refs")
        ensure_ref_items(self.evidence_refs, "PluginRegistryDeltaItem.evidence_refs")
        ensure_schema_version(self.schema_version, "PluginRegistryDeltaItem.schema_version")
        if self.item_digest:
            ensure_ref_text(self.item_digest, "PluginRegistryDeltaItem.item_digest")
        else:
            object.__setattr__(self, "item_digest", registry_canonical_digest(self))


@dataclass(frozen=True, slots=True)
class PluginRegistryDelta:
    delta_ref: str
    base_snapshot_ref: str
    target_snapshot_ref: str
    added: tuple[PluginRegistryDeltaItem, ...] = field(default_factory=tuple)
    removed: tuple[PluginRegistryDeltaItem, ...] = field(default_factory=tuple)
    changed: tuple[PluginRegistryDeltaItem, ...] = field(default_factory=tuple)
    unchanged: tuple[PluginRegistryDeltaItem, ...] = field(default_factory=tuple)
    conflict_refs: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    audit_index_ref: str = ""
    conflict_report_ref: str = ""
    actor_ref: str = ""
    scope_ref: str = ""
    trace_ref: str = ""
    policy_ref: str = ""
    approval_ref: str = ""
    responsibility_chain_ref: str = ""
    accountability_ref: str = ""
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    tamper_evidence_ref: str = ""
    delta_digest: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.delta_ref, "PluginRegistryDelta.delta_ref")
        ensure_ref_text(self.base_snapshot_ref, "PluginRegistryDelta.base_snapshot_ref")
        ensure_ref_text(self.target_snapshot_ref, "PluginRegistryDelta.target_snapshot_ref")
        for attr in ("added", "removed", "changed", "unchanged"):
            for item in getattr(self, attr):
                if not isinstance(item, PluginRegistryDeltaItem):
                    raise ValueError(f"PluginRegistryDelta.{attr} must contain PluginRegistryDeltaItem")
        ensure_ref_items(self.conflict_refs, "PluginRegistryDelta.conflict_refs")
        ensure_ref_items(self.evidence_refs, "PluginRegistryDelta.evidence_refs")
        for name in ("audit_index_ref", "conflict_report_ref", "actor_ref", "scope_ref", "trace_ref", "policy_ref", "approval_ref", "responsibility_chain_ref", "accountability_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, name), f"PluginRegistryDelta.{name}", required=False)
        ensure_ref_items(self.provenance_refs, "PluginRegistryDelta.provenance_refs")
        ensure_schema_version(self.schema_version, "PluginRegistryDelta.schema_version")
        if self.delta_digest:
            ensure_ref_text(self.delta_digest, "PluginRegistryDelta.delta_digest")
        else:
            object.__setattr__(self, "delta_digest", registry_canonical_digest(self))


def _record_map(snapshot: PluginRegistrySnapshot) -> dict[str, PluginRegistryRecord]:
    return {record.registry_key_text: record for record in snapshot.records if record.registry_key is not None}


def _changed_fields(base: PluginRegistryRecord, target: PluginRegistryRecord) -> tuple[str, ...]:
    fields: list[str] = []
    for name in (
        "manifest_hash", "package_ref", "entry_ref", "source_trust_ref", "signature_ref",
        "permission_decl_ref", "resource_decl_ref", "credential_decl_ref", "data_governance_decl_ref",
        "audit_decl_ref", "version_decl_ref", "rollback_decl_ref", "compatibility_decl_ref",
        "hot_switch_decl_ref", "migration_ref", "replay_compatibility_ref", "breaking_change_policy_ref", "summary",
    ):
        if getattr(base, name) != getattr(target, name):
            fields.append(name)
    return tuple(fields)


def build_registry_delta(delta_ref: str, base: PluginRegistrySnapshot, target: PluginRegistrySnapshot) -> PluginRegistryDelta:
    base_map = _record_map(base)
    target_map = _record_map(target)
    added: list[PluginRegistryDeltaItem] = []
    removed: list[PluginRegistryDeltaItem] = []
    changed: list[PluginRegistryDeltaItem] = []
    unchanged: list[PluginRegistryDeltaItem] = []
    for key_text in sorted(set(base_map) | set(target_map)):
        base_record = base_map.get(key_text)
        target_record = target_map.get(key_text)
        if base_record is None and target_record is not None:
            added.append(PluginRegistryDeltaItem(DELTA_ITEM_ADDED, target_record.registry_key, target_record_digest=target_record.canonical_record_digest, evidence_refs=("evidence:delta_added",)))
        elif target_record is None and base_record is not None:
            removed.append(PluginRegistryDeltaItem(DELTA_ITEM_REMOVED, base_record.registry_key, base_record_digest=base_record.canonical_record_digest, evidence_refs=("evidence:delta_removed",)))
        elif base_record is not None and target_record is not None:
            fields = _changed_fields(base_record, target_record)
            if base_record.canonical_record_digest != target_record.canonical_record_digest:
                changed.append(PluginRegistryDeltaItem(DELTA_ITEM_CHANGED, target_record.registry_key, base_record_digest=base_record.canonical_record_digest, target_record_digest=target_record.canonical_record_digest, changed_fields=fields, evidence_refs=("evidence:delta_changed",)))
            else:
                unchanged.append(PluginRegistryDeltaItem(DELTA_ITEM_UNCHANGED, target_record.registry_key, base_record_digest=base_record.canonical_record_digest, target_record_digest=target_record.canonical_record_digest, evidence_refs=("evidence:delta_unchanged",)))
    return PluginRegistryDelta(
        delta_ref=delta_ref,
        base_snapshot_ref=base.snapshot_ref,
        target_snapshot_ref=target.snapshot_ref,
        added=tuple(added),
        removed=tuple(removed),
        changed=tuple(changed),
        unchanged=tuple(unchanged),
        evidence_refs=("evidence:registry_delta",),
        trace_ref=target.trace_ref or base.trace_ref,
    )
