from dataclasses import FrozenInstanceError

import pytest

from tiangong_kernel.l5_plugin_host import PluginRegistryDataOnlyResult, PluginRegistryEntry, PluginRegistrySnapshot


def build_entry() -> PluginRegistryEntry:
    return PluginRegistryEntry(
        entry_ref="registry_entry:memory_stub",
        plugin_id="plugin:memory_stub",
        manifest_ref="manifest:memory_stub",
        package_ref="package:memory_stub",
        declared_mount_surfaces=("skill_surface_decl",),
        declared_boundary_refs=("boundary:no_live_action",),
        declared_audit_refs=("audit:anchor",),
        actor_ref="actor:engineer",
        scope_ref="scope:l5_phase1",
        trace_ref="trace:registry",
        policy_ref="policy:phase1",
        evidence_refs=("evidence:registry",),
        provenance_refs=("provenance:l4",),
        accountability_ref="accountability:owner",
        tamper_evidence_ref="tamper:registry",
    )


def test_registry_entry_and_snapshot_are_frozen_data_items():
    entry = build_entry()
    snapshot = PluginRegistrySnapshot(
        snapshot_ref="registry_snapshot:phase1",
        entries=(entry,),
        actor_ref="actor:engineer",
        scope_ref="scope:l5_phase1",
        trace_ref="trace:snapshot",
        policy_ref="policy:phase1",
        evidence_refs=("evidence:snapshot",),
        provenance_refs=("provenance:l4",),
        accountability_ref="accountability:owner",
        tamper_evidence_ref="tamper:snapshot",
    )
    assert snapshot.entries == (entry,)
    assert snapshot.registry_snapshot_digest
    with pytest.raises(FrozenInstanceError):
        snapshot.entries = ()


def test_registry_snapshot_exposes_no_mutating_registry_methods():
    snapshot = PluginRegistrySnapshot(snapshot_ref="registry_snapshot:empty")
    method_names = set(dir(snapshot))
    for name in ("register", "unregister", "update", "enable", "disable"):
        assert name not in method_names


def test_registry_data_only_result_does_not_mutate_snapshot():
    result = PluginRegistryDataOnlyResult(
        result_ref="registry_result:view_only",
        entry_ref="registry_entry:memory_stub",
        accepted_as_view=True,
        reason="只表达登记视图，不写注册表。",
        evidence_refs=("evidence:registry_result",),
    )
    assert result.accepted_as_view is True
