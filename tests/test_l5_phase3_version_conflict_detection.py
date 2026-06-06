from l5_phase3_sample_factory import complete_record, complete_snapshot, registry_namespace
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind, PluginRegistryValidator


def test_same_version_different_hash_is_plugin_version_conflict():
    first = complete_record(registry_record_ref="record:first")
    second = complete_record(registry_record_ref="record:second", manifest_hash="b" * 64, manifest_digest_value="b" * 64)
    report = PluginRegistryValidator(validator_ref="validator:test").validate(complete_snapshot((first, second)), (registry_namespace(),))
    assert any(c.kind is PluginRegistryConflictKind.PLUGIN_VERSION_CONFLICT for c in report.conflicts)
