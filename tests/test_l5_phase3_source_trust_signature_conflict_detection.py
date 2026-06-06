from l5_phase3_sample_factory import complete_record, complete_snapshot, registry_namespace
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind, PluginRegistryValidator


def test_missing_source_trust_and_signature_refs_are_conflicts():
    record = complete_record(source_trust_ref="", signature_ref="")
    report = PluginRegistryValidator(validator_ref="validator:test").validate(complete_snapshot((record,)), (registry_namespace(),))
    kinds = {c.kind for c in report.conflicts}
    assert PluginRegistryConflictKind.SOURCE_TRUST_CONFLICT in kinds
    assert PluginRegistryConflictKind.SIGNATURE_REF_CONFLICT in kinds
