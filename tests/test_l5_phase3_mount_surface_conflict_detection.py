from l5_phase3_sample_factory import complete_record, complete_snapshot, registry_key, registry_namespace
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind, PluginRegistryValidator


def test_exclusive_mount_surface_collision_is_conflict():
    first = complete_record(registry_record_ref="record:first")
    second = complete_record(registry_record_ref="record:second", registry_key=registry_key("plugin:other", "version:1"))
    report = PluginRegistryValidator(validator_ref="validator:test").validate(complete_snapshot((first, second)), (registry_namespace(),))
    assert any(c.kind is PluginRegistryConflictKind.MOUNT_SURFACE_CONFLICT for c in report.conflicts)
