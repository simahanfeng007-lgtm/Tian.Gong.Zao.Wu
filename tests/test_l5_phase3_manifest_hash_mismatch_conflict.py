from l5_phase3_sample_factory import complete_record, complete_snapshot, registry_namespace
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind, PluginRegistryValidator


def test_manifest_hash_mismatch_reports_conflict():
    record = complete_record(manifest_digest_value="b" * 64)
    report = PluginRegistryValidator(validator_ref="validator:test").validate(complete_snapshot((record,)), (registry_namespace(),))
    assert any(c.kind is PluginRegistryConflictKind.MANIFEST_HASH_MISMATCH for c in report.conflicts)
