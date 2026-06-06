from dataclasses import fields

from tiangong_kernel.l5_plugin_host import PluginManifestView, PluginRegistryEntry, PluginRegistrySnapshot

_REQUIRED = {
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
}


def test_manifest_registry_and_snapshot_expose_accountability_fields():
    for cls in (PluginManifestView, PluginRegistryEntry, PluginRegistrySnapshot):
        names = {field.name for field in fields(cls)}
        assert _REQUIRED.issubset(names)


def test_readiness_fields_can_be_populated_on_registry_entry():
    entry = PluginRegistryEntry(
        entry_ref="registry_entry:accountable",
        plugin_id="plugin:accountable",
        manifest_ref="manifest:accountable",
        actor_ref="actor:engineer",
        scope_ref="scope:l5_phase1",
        trace_ref="trace:registry",
        policy_ref="policy:phase1",
        evidence_refs=("evidence:registry",),
        provenance_refs=("provenance:l4",),
        accountability_ref="accountability:owner",
        tamper_evidence_ref="tamper:registry",
    )
    assert entry.accountability_ref == "accountability:owner"
