from l5_phase3_sample_factory import complete_record, complete_snapshot, registry_namespace
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind, PluginRegistryValidator


def test_missing_permission_and_resource_refs_are_conflicts():
    record = complete_record(permission_decl_ref="", resource_decl_ref="")
    report = PluginRegistryValidator(validator_ref="validator:test").validate(complete_snapshot((record,)), (registry_namespace(),))
    kinds = {c.kind for c in report.conflicts}
    assert PluginRegistryConflictKind.PERMISSION_DECL_CONFLICT in kinds
    assert PluginRegistryConflictKind.RESOURCE_DECL_CONFLICT in kinds
