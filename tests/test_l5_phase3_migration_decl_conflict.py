from l5_phase3_sample_factory import complete_record, complete_snapshot, registry_namespace
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind, PluginRegistryValidator


def test_missing_migration_or_upcast_policy_is_conflict():
    record = complete_record(migration_ref="", upcast_policy_ref="")
    report = PluginRegistryValidator(validator_ref="validator:test").validate(complete_snapshot((record,)), (registry_namespace(),))
    assert any(c.kind is PluginRegistryConflictKind.MIGRATION_DECL_CONFLICT for c in report.conflicts)
