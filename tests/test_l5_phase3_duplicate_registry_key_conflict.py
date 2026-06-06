from l5_phase3_sample_factory import complete_record, complete_snapshot, registry_namespace
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind, PluginRegistryValidator


def test_duplicate_registry_key_is_p1_conflict():
    first = complete_record(registry_record_ref="record:first")
    second = complete_record(registry_record_ref="record:second")
    report = PluginRegistryValidator(validator_ref="validator:test").validate(complete_snapshot((first, second)), (registry_namespace(),))
    conflicts = [c for c in report.conflicts if c.kind is PluginRegistryConflictKind.DUPLICATE_REGISTRY_KEY]
    assert conflicts and conflicts[0].blocking
