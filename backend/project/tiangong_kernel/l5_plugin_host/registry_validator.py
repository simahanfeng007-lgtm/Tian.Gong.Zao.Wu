"""L5 phase 3 pure registry validator.

The validator consumes explicit in-memory RegistryRecord declarations and
returns conflict reports. It never scans the filesystem, discovers plugins,
imports plugin code, mutates snapshots, writes registries, or performs lifecycle
actions.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_text, ensure_schema_version
from .registry_conflict import (
    PluginRegistryConflict,
    PluginRegistryConflictKind,
    PluginRegistryConflictReport,
    PluginRegistryConflictSeverity,
)
from .registry_conflict_rules import (
    PluginRegistryConflictRuleSet,
    find_inert_pattern_hits,
    find_plain_credential_hits,
)
from .registry_namespace import (
    NAMESPACE_POLICY_EXPLICIT_ALIAS_REQUIRED,
    NAMESPACE_POLICY_FROZEN_ARCHIVE,
    NAMESPACE_POLICY_MULTI_VERSION_ALLOWED,
    NAMESPACE_POLICY_SINGLE_PLUGIN_ID,
    PluginRegistryNamespace,
)
from .registry_record import PluginRegistryRecord
from .registry_snapshot import PluginRegistrySnapshot


def _has_text(value: str) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_tuple(value: tuple[str, ...]) -> bool:
    return isinstance(value, tuple) and bool(value)


def _severity_blocking(severity: PluginRegistryConflictSeverity) -> bool:
    return severity in (PluginRegistryConflictSeverity.P0, PluginRegistryConflictSeverity.P1)


@dataclass(frozen=True, slots=True)
class PluginRegistryValidator:
    validator_ref: str
    rule_set: PluginRegistryConflictRuleSet = field(default_factory=lambda: PluginRegistryConflictRuleSet(rule_set_ref="rule_set:l5_phase3_registry"))
    supported_schema_versions: tuple[str, ...] = ("0.2", "0.3", "0.1")
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.validator_ref, "PluginRegistryValidator.validator_ref")
        if not isinstance(self.rule_set, PluginRegistryConflictRuleSet):
            raise ValueError("PluginRegistryValidator.rule_set must be PluginRegistryConflictRuleSet")
        ensure_schema_version(self.schema_version, "PluginRegistryValidator.schema_version")

    def validate(self, snapshot: PluginRegistrySnapshot, namespaces: tuple[PluginRegistryNamespace, ...] = tuple()) -> PluginRegistryConflictReport:
        if not isinstance(snapshot, PluginRegistrySnapshot):
            raise ValueError("PluginRegistryValidator.validate requires PluginRegistrySnapshot")
        namespace_by_id = {item.namespace_id: item for item in namespaces}
        conflicts: list[PluginRegistryConflict] = []

        def add(kind: PluginRegistryConflictKind, severity: PluginRegistryConflictSeverity, message: str, records: tuple[PluginRegistryRecord, ...], field_path: str) -> None:
            refs = tuple(record.registry_record_ref for record in records)
            conflicts.append(
                PluginRegistryConflict(
                    conflict_ref=f"conflict:{kind.value}:{len(conflicts) + 1}",
                    kind=kind,
                    severity=severity,
                    message=message,
                    affected_record_refs=refs,
                    field_path=field_path,
                    blocking=_severity_blocking(severity),
                    evidence_refs=("evidence:l5_phase3_registry_conflict",),
                    trace_ref=snapshot.trace_ref,
                    responsibility_chain_ref=snapshot.responsibility_chain_ref,
                )
            )

        key_map: dict[str, list[PluginRegistryRecord]] = defaultdict(list)
        plugin_map: dict[tuple[str, str, str], list[PluginRegistryRecord]] = defaultdict(list)
        version_map: dict[tuple[str, str, str, str], list[PluginRegistryRecord]] = defaultdict(list)
        exclusive_surface_map: dict[str, list[PluginRegistryRecord]] = defaultdict(list)

        for record in snapshot.records:
            if record.registry_key is not None:
                key_map[record.registry_key_text].append(record)
                plugin_map[(record.namespace, record.plugin_id, record.plugin_kind)].append(record)
                version_map[(record.namespace, record.plugin_id, record.plugin_kind, record.version_identity)].append(record)
            for surface in record.exclusive_mount_surface_refs:
                exclusive_surface_map[surface].append(record)
            self._validate_record_required_fields(record, add)
            self._validate_record_patterns(record, add)
            self._validate_record_version_refs(record, add)

        for records in key_map.values():
            if len(records) > 1:
                add(PluginRegistryConflictKind.DUPLICATE_REGISTRY_KEY, PluginRegistryConflictSeverity.P1, "registry_key is duplicated", tuple(records), "registry_key")

        for key, records in plugin_map.items():
            namespace_id = key[0]
            namespace = namespace_by_id.get(namespace_id)
            policy = namespace.uniqueness_policy if namespace is not None else NAMESPACE_POLICY_MULTI_VERSION_ALLOWED
            if policy == NAMESPACE_POLICY_SINGLE_PLUGIN_ID and len(records) > 1:
                add(PluginRegistryConflictKind.DUPLICATE_PLUGIN_ID, PluginRegistryConflictSeverity.P1, "namespace policy requires plugin_id uniqueness", tuple(records), "registry_key.plugin_id")
            if policy == NAMESPACE_POLICY_EXPLICIT_ALIAS_REQUIRED and len(records) > 1:
                missing_alias = tuple(record for record in records if not (record.alias_ref or record.channel_ref))
                if missing_alias:
                    add(PluginRegistryConflictKind.DUPLICATE_PLUGIN_ID, PluginRegistryConflictSeverity.P1, "multi-version plugin_id requires alias_ref or channel_ref", missing_alias, "alias_ref")
            if policy == NAMESPACE_POLICY_FROZEN_ARCHIVE:
                revision_refs = {record.updated_at_ref for record in records if record.updated_at_ref}
                if len(records) > 1 and (not namespace.revision_ref or len(revision_refs) <= 1):
                    add(PluginRegistryConflictKind.NAMESPACE_COLLISION, PluginRegistryConflictSeverity.P2, "frozen archive duplicate plugin_id requires revision distinction", tuple(records), "namespace.revision_ref")

        for records in version_map.values():
            if len(records) > 1:
                hashes = {record.manifest_hash for record in records}
                if len(hashes) > 1:
                    add(PluginRegistryConflictKind.PLUGIN_VERSION_CONFLICT, PluginRegistryConflictSeverity.P1, "same plugin version has different manifest hash", tuple(records), "manifest_hash")
                entry_refs = {record.entry_ref for record in records}
                if len(entry_refs) > 1:
                    add(PluginRegistryConflictKind.ENTRY_REF_CONFLICT, PluginRegistryConflictSeverity.P2, "same plugin version has different entry_ref", tuple(records), "entry_ref")

        for records in exclusive_surface_map.values():
            if len(records) > 1:
                add(PluginRegistryConflictKind.MOUNT_SURFACE_CONFLICT, PluginRegistryConflictSeverity.P2, "exclusive mount surface is shared by multiple records", tuple(records), "exclusive_mount_surface_refs")

        return PluginRegistryConflictReport(
            report_ref=f"conflict_report:{snapshot.snapshot_ref}",
            conflicts=tuple(conflicts),
            actor_ref=snapshot.actor_ref,
            scope_ref=snapshot.scope_ref,
            trace_ref=snapshot.trace_ref,
            policy_ref=snapshot.policy_ref,
            approval_ref=snapshot.approval_ref,
            responsibility_chain_ref=snapshot.responsibility_chain_ref,
            accountability_ref=snapshot.accountability_ref,
            provenance_refs=snapshot.provenance_refs,
            evidence_refs=snapshot.evidence_refs or ("evidence:l5_phase3_registry_report",),
            tamper_evidence_ref=snapshot.tamper_evidence_ref,
            observed_summary="passed" if not conflicts else "conflicts_detected",
        )

    def _validate_record_required_fields(self, record: PluginRegistryRecord, add) -> None:
        if record.registry_key is None:
            add(PluginRegistryConflictKind.DUPLICATE_REGISTRY_KEY, PluginRegistryConflictSeverity.P1, "registry_key is required", (record,), "registry_key")
        for field_name, kind in (
            ("manifest_ref", PluginRegistryConflictKind.MANIFEST_HASH_MISMATCH),
            ("manifest_hash", PluginRegistryConflictKind.MANIFEST_HASH_MISMATCH),
            ("package_ref", PluginRegistryConflictKind.NAMESPACE_COLLISION),
            ("entry_ref", PluginRegistryConflictKind.ENTRY_REF_CONFLICT),
            ("permission_decl_ref", PluginRegistryConflictKind.PERMISSION_DECL_CONFLICT),
            ("resource_decl_ref", PluginRegistryConflictKind.RESOURCE_DECL_CONFLICT),
            ("credential_decl_ref", PluginRegistryConflictKind.CREDENTIAL_DECL_CONFLICT),
            ("data_governance_decl_ref", PluginRegistryConflictKind.DATA_GOVERNANCE_CONFLICT),
            ("audit_decl_ref", PluginRegistryConflictKind.AUDIT_DECL_CONFLICT),
            ("version_decl_ref", PluginRegistryConflictKind.PLUGIN_VERSION_CONFLICT),
            ("rollback_decl_ref", PluginRegistryConflictKind.ROLLBACK_DECL_CONFLICT),
            ("compatibility_decl_ref", PluginRegistryConflictKind.COMPATIBILITY_DECL_CONFLICT),
            ("source_trust_ref", PluginRegistryConflictKind.SOURCE_TRUST_CONFLICT),
            ("signature_ref", PluginRegistryConflictKind.SIGNATURE_REF_CONFLICT),
            ("hot_switch_decl_ref", PluginRegistryConflictKind.HOT_SWITCH_DECL_CONFLICT),
            ("migration_ref", PluginRegistryConflictKind.MIGRATION_DECL_CONFLICT),
            ("replay_compatibility_ref", PluginRegistryConflictKind.REPLAY_COMPATIBILITY_CONFLICT),
            ("breaking_change_policy_ref", PluginRegistryConflictKind.BREAKING_CHANGE_CONFLICT),
        ):
            if not _has_text(getattr(record, field_name)):
                severity = PluginRegistryConflictSeverity.P1 if field_name in ("manifest_ref", "manifest_hash") else PluginRegistryConflictSeverity.P2
                add(kind, severity, f"{field_name} is required", (record,), field_name)
        for field_name in ("actor_ref", "scope_ref", "trace_ref", "policy_ref", "responsibility_chain_ref"):
            if not _has_text(getattr(record, field_name)):
                add(PluginRegistryConflictKind.RESPONSIBILITY_CHAIN_CONFLICT, PluginRegistryConflictSeverity.P1, f"{field_name} is required for registry accountability", (record,), field_name)
        if not _has_tuple(record.evidence_refs):
            add(PluginRegistryConflictKind.RESPONSIBILITY_CHAIN_CONFLICT, PluginRegistryConflictSeverity.P1, "evidence_refs are required", (record,), "evidence_refs")
        if record.manifest_digest_value and record.manifest_hash and record.manifest_digest_value != record.manifest_hash:
            add(PluginRegistryConflictKind.MANIFEST_HASH_MISMATCH, PluginRegistryConflictSeverity.P1, "manifest_hash does not match manifest digest value", (record,), "manifest_hash")
        if record.schema_version_text and record.schema_version_text not in self.supported_schema_versions:
            add(PluginRegistryConflictKind.SCHEMA_VERSION_MISMATCH, PluginRegistryConflictSeverity.P2, "schema_version_text is outside supported declaration range", (record,), "schema_version_text")
        if not record.upcast_policy_ref:
            add(PluginRegistryConflictKind.MIGRATION_DECL_CONFLICT, PluginRegistryConflictSeverity.P2, "upcast_policy_ref is required with migration_ref", (record,), "upcast_policy_ref")

    def _validate_record_patterns(self, record: PluginRegistryRecord, add) -> None:
        credential_hits = find_plain_credential_hits(record)
        if credential_hits:
            add(PluginRegistryConflictKind.CREDENTIAL_DECL_CONFLICT, PluginRegistryConflictSeverity.P0, "record contains suspected plain credential value", (record,), credential_hits[0])
        live_hits = find_inert_pattern_hits(record, self.rule_set.live_action_patterns)
        if live_hits:
            add(PluginRegistryConflictKind.LIVE_ACTION_CONFLICT, PluginRegistryConflictSeverity.P0, "record declaration contains live action pattern", (record,), live_hits[0])
        legacy_hits = find_inert_pattern_hits(record, self.rule_set.legacy_runtime_patterns)
        if legacy_hits:
            add(PluginRegistryConflictKind.LEGACY_RUNTIME_CONFLICT, PluginRegistryConflictSeverity.P0, "record declaration contains legacy runtime pattern", (record,), legacy_hits[0])
        l6_hits = find_inert_pattern_hits(record, self.rule_set.l6_implementation_patterns)
        if l6_hits:
            add(PluginRegistryConflictKind.L6_IMPLEMENTATION_CONFLICT, PluginRegistryConflictSeverity.P0, "record declaration contains L6 implementation pattern", (record,), l6_hits[0])

    def _validate_record_version_refs(self, record: PluginRegistryRecord, add) -> None:
        # Third stage does not parse semver. It only reports incomparable but risky
        # version text as warning/P3 when explicit compatibility is absent.
        if record.plugin_version_text and "." not in record.plugin_version_text and not record.compatibility_decl_ref:
            add(PluginRegistryConflictKind.PLUGIN_VERSION_CONFLICT, PluginRegistryConflictSeverity.P3, "plugin_version_text is not comparable and compatibility ref is absent", (record,), "plugin_version_text")
