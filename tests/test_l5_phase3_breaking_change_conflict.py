from l5_phase3_sample_factory import complete_record, complete_snapshot, registry_namespace
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind, PluginRegistryValidator


def test_missing_breaking_change_policy_is_conflict():
    record = complete_record(breaking_change_policy_ref="")
    report = PluginRegistryValidator(validator_ref="validator:test").validate(complete_snapshot((record,)), (registry_namespace(),))
    assert any(c.kind is PluginRegistryConflictKind.BREAKING_CHANGE_CONFLICT for c in report.conflicts)
