from dataclasses import FrozenInstanceError, fields

import pytest

from tiangong_kernel.l5_plugin_host import PluginManifestView, to_l5_digest, to_l5_primitive

_ALLOWED = {
    "plugin_id",
    "name",
    "version",
    "kind",
    "declared_entry_ref",
    "declared_permissions",
    "declared_dependencies",
    "declared_lifecycle",
    "declared_boundary_refs",
    "declared_audit_refs",
    "summary",
    "actor_ref",
    "scope_ref",
    "trace_ref",
    "policy_ref",
    "approval_ref",
    "handoff_ref",
    "evidence_refs",
    "provenance_refs",
    "accountability_ref",
    "tamper_evidence_ref",
    "validation_requirement_refs",
    "verification_requirement_refs",
    "evaluation_requirement_refs",
    "regression_requirement_refs",
    "rollback_requirement_refs",
    "health_requirement_refs",
    "manifest_digest",
    "schema_version",
}


def build_manifest() -> PluginManifestView:
    return PluginManifestView(
        plugin_id="plugin:memory_stub",
        name="memory declaration",
        version="0.1.0",
        kind="subsystem_declaration",
        declared_entry_ref="entry:memory_stub",
        declared_permissions=("permission:read_only",),
        declared_dependencies=("dependency:none",),
        declared_lifecycle=("declared_only",),
        declared_boundary_refs=("boundary:no_live_action",),
        declared_audit_refs=("audit:anchor",),
        actor_ref="actor:engineer",
        scope_ref="scope:l5_phase1",
        trace_ref="trace:manifest",
        policy_ref="policy:phase1",
        handoff_ref="handoff:l4_to_l5",
        evidence_refs=("evidence:manifest",),
        provenance_refs=("provenance:l4",),
        accountability_ref="accountability:owner",
        tamper_evidence_ref="tamper:manifest",
        validation_requirement_refs=("validation:phase1",),
        verification_requirement_refs=("verification:phase1",),
        evaluation_requirement_refs=("evaluation:phase1",),
        regression_requirement_refs=("regression:phase1",),
        rollback_requirement_refs=("rollback:ref_only",),
        health_requirement_refs=("health:ref_only",),
        summary="只读声明。",
    )


def test_manifest_view_uses_phase1_field_whitelist():
    names = {field.name for field in fields(PluginManifestView)}
    assert names == _ALLOWED


def test_manifest_view_digest_is_stable_and_data_only():
    first = build_manifest()
    second = build_manifest()
    assert first.manifest_digest == second.manifest_digest
    assert to_l5_digest(first) == to_l5_digest(second)
    primitive = to_l5_primitive(first)
    assert primitive["declared_entry_ref"] == "entry:memory_stub"
    assert "manifest_digest" in primitive
    with pytest.raises(FrozenInstanceError):
        first.name = "changed"


def test_manifest_view_rejects_real_paths_and_callable_entry_values():
    with pytest.raises(ValueError):
        PluginManifestView(
            plugin_id="plugin:bad",
            name="bad",
            version="0.1.0",
            kind="bad",
            declared_entry_ref="plugins/bad.py",
        )
    with pytest.raises(ValueError):
        PluginManifestView(
            plugin_id="plugin:bad",
            name="bad",
            version="0.1.0",
            kind="bad",
            declared_entry_ref=lambda: None,
        )
