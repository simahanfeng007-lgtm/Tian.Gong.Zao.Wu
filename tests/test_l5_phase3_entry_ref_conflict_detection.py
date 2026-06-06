from l5_phase3_sample_factory import complete_record, complete_snapshot, registry_namespace
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind, PluginRegistryValidator


def test_same_version_different_entry_ref_is_entry_conflict():
    first = complete_record(registry_record_ref="record:first")
    second = complete_record(registry_record_ref="record:second", entry_ref="entry:other")
    report = PluginRegistryValidator(validator_ref="validator:test").validate(complete_snapshot((first, second)), (registry_namespace(),))
    assert any(c.kind is PluginRegistryConflictKind.ENTRY_REF_CONFLICT for c in report.conflicts)
