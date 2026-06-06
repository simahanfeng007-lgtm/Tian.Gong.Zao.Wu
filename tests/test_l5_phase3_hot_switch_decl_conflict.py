from l5_phase3_sample_factory import complete_record, complete_snapshot, registry_namespace
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind, PluginRegistryValidator


def test_hot_switch_decl_conflict_detects_missing_decl():
    record = complete_record(hot_switch_decl_ref="")
    report = PluginRegistryValidator(validator_ref="validator:test").validate(complete_snapshot((record,)), (registry_namespace(),))
    assert PluginRegistryConflictKind.HOT_SWITCH_DECL_CONFLICT in {c.kind for c in report.conflicts}
