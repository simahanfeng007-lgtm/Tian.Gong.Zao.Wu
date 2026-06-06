"""L5 phase 3 safe registry public projection declarations."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text, ensure_text_items
from .registry_conflict import PluginRegistryConflictReport
from .registry_record import PluginRegistryRecord
from .registry_snapshot import PluginRegistrySnapshot


def _redact_ref(value: str) -> str:
    if not value:
        return ""
    if value.startswith("redacted:"):
        return value
    tail = value.rsplit(":", 1)[-1]
    return f"redacted:{tail[:24].rstrip("_:-")}"


def _redact_refs(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_redact_ref(value) for value in values)


@dataclass(frozen=True, slots=True)
class PluginRegistryProjectionSummary:
    ref: str
    summary: str
    severity: str = "info"
    evidence: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.ref, "PluginRegistryProjectionSummary.ref", required=False)
        ensure_short_text(self.summary, "PluginRegistryProjectionSummary.summary")
        ensure_ref_text(self.severity, "PluginRegistryProjectionSummary.severity")
        ensure_ref_text(self.evidence, "PluginRegistryProjectionSummary.evidence", required=False)
        ensure_schema_version(self.schema_version, "PluginRegistryProjectionSummary.schema_version")


@dataclass(frozen=True, slots=True)
class PluginRegistryCredentialSummary:
    credential_kind: str
    credential_policy_ref: str
    redaction_state: str
    boundary_ref: str
    required_confirmation_ref: str = ""
    evidence_ref: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.credential_kind, "PluginRegistryCredentialSummary.credential_kind")
        ensure_ref_text(self.credential_policy_ref, "PluginRegistryCredentialSummary.credential_policy_ref")
        ensure_ref_text(self.redaction_state, "PluginRegistryCredentialSummary.redaction_state")
        ensure_ref_text(self.boundary_ref, "PluginRegistryCredentialSummary.boundary_ref")
        ensure_ref_text(self.required_confirmation_ref, "PluginRegistryCredentialSummary.required_confirmation_ref", required=False)
        ensure_ref_text(self.evidence_ref, "PluginRegistryCredentialSummary.evidence_ref", required=False)
        ensure_schema_version(self.schema_version, "PluginRegistryCredentialSummary.schema_version")


@dataclass(frozen=True, slots=True)
class PluginRegistryPublicProjection:
    projection_ref: str
    plugin_id: str
    plugin_name: str
    plugin_kind: str
    namespace: str
    version_text: str = ""
    version_ref: str = ""
    manifest_hash: str = ""
    mount_surface_summary: str = ""
    permission_summary: str = ""
    resource_summary: str = ""
    credential_summary: PluginRegistryCredentialSummary | None = None
    data_governance_summary: str = ""
    audit_summary: str = ""
    compatibility_summary: str = ""
    conflict_summary: str = ""
    snapshot_delta_summary: str = ""
    migration_summary: PluginRegistryProjectionSummary | None = None
    rollback_summary: PluginRegistryProjectionSummary | None = None
    hot_switch_summary: PluginRegistryProjectionSummary | None = None
    replay_compatibility_summary: PluginRegistryProjectionSummary | None = None
    breaking_change_summary: PluginRegistryProjectionSummary | None = None
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    risk_tags: tuple[str, ...] = field(default_factory=tuple)
    status_text: str = "declared_only"
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("projection_ref", "plugin_id", "plugin_name", "plugin_kind", "namespace"):
            ensure_ref_text(getattr(self, name), f"PluginRegistryPublicProjection.{name}")
        for name in ("version_text", "version_ref", "manifest_hash", "status_text"):
            ensure_ref_text(getattr(self, name), f"PluginRegistryPublicProjection.{name}", required=False)
        for name in ("mount_surface_summary", "permission_summary", "resource_summary", "data_governance_summary", "audit_summary", "compatibility_summary", "conflict_summary", "snapshot_delta_summary"):
            ensure_short_text(getattr(self, name), f"PluginRegistryPublicProjection.{name}")
        if self.credential_summary is not None and not isinstance(self.credential_summary, PluginRegistryCredentialSummary):
            raise ValueError("PluginRegistryPublicProjection.credential_summary must be PluginRegistryCredentialSummary or None")
        for name in ("migration_summary", "rollback_summary", "hot_switch_summary", "replay_compatibility_summary", "breaking_change_summary"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, PluginRegistryProjectionSummary):
                raise ValueError(f"PluginRegistryPublicProjection.{name} must be PluginRegistryProjectionSummary or None")
        ensure_ref_items(self.evidence_refs, "PluginRegistryPublicProjection.evidence_refs")
        if any(not ref.startswith("redacted:") for ref in self.evidence_refs):
            raise ValueError("PluginRegistryPublicProjection.evidence_refs must be redacted refs")
        ensure_text_items(self.risk_tags, "PluginRegistryPublicProjection.risk_tags")
        ensure_schema_version(self.schema_version, "PluginRegistryPublicProjection.schema_version")


def public_projection_from_record(record: PluginRegistryRecord, snapshot: PluginRegistrySnapshot, conflict_report: PluginRegistryConflictReport) -> PluginRegistryPublicProjection:
    conflict_count = len(tuple(conflict for conflict in conflict_report.conflicts if record.registry_record_ref in conflict.affected_record_refs))
    return PluginRegistryPublicProjection(
        projection_ref=f"projection:{record.registry_record_ref}",
        plugin_id=record.plugin_id,
        plugin_name=record.summary or record.plugin_id,
        plugin_kind=record.plugin_kind,
        namespace=record.namespace,
        version_text=record.plugin_version_text,
        version_ref=record.plugin_version_ref or record.version_identity,
        manifest_hash=record.manifest_hash,
        mount_surface_summary=f"count={len(record.mount_surface_refs)}",
        permission_summary=f"tags={len(record.permission_tags)};ref={record.permission_decl_ref}",
        resource_summary=f"tags={len(record.resource_tags)};ref={record.resource_decl_ref}",
        credential_summary=PluginRegistryCredentialSummary(
            credential_kind="declared_handle_ref_only",
            credential_policy_ref=record.credential_decl_ref,
            redaction_state="redacted",
            boundary_ref=record.trust_boundary_decl_ref or "boundary:credential:redacted",
            required_confirmation_ref=record.policy_ref,
            evidence_ref=_redact_ref(record.evidence_refs[0] if record.evidence_refs else "evidence:registry"),
        ),
        data_governance_summary=f"ref={record.data_governance_decl_ref}",
        audit_summary=f"ref={record.audit_decl_ref}",
        compatibility_summary=f"ref={record.compatibility_decl_ref}",
        conflict_summary=f"count={conflict_count}",
        snapshot_delta_summary=f"snapshot={snapshot.snapshot_ref};digest={snapshot.snapshot_digest[:12]}",
        migration_summary=PluginRegistryProjectionSummary(ref=record.migration_ref, summary="migration declaration ref only", evidence=_redact_ref(record.evidence_refs[0] if record.evidence_refs else "evidence:migration")),
        rollback_summary=PluginRegistryProjectionSummary(ref=record.rollback_decl_ref, summary="rollback declaration ref only", evidence=_redact_ref(record.evidence_refs[0] if record.evidence_refs else "evidence:rollback")),
        hot_switch_summary=PluginRegistryProjectionSummary(ref=record.hot_switch_decl_ref, summary="hot-switch declaration ref only", evidence=_redact_ref(record.evidence_refs[0] if record.evidence_refs else "evidence:hot_switch")),
        replay_compatibility_summary=PluginRegistryProjectionSummary(ref=record.replay_compatibility_ref, summary="replay compatibility declaration ref only", evidence=_redact_ref(record.evidence_refs[0] if record.evidence_refs else "evidence:replay")),
        breaking_change_summary=PluginRegistryProjectionSummary(ref=record.breaking_change_policy_ref, summary="breaking change policy ref only", evidence=_redact_ref(record.evidence_refs[0] if record.evidence_refs else "evidence:breaking_change")),
        evidence_refs=_redact_refs(record.evidence_refs),
        risk_tags=record.permission_tags,
        status_text=record.status_ref,
    )
