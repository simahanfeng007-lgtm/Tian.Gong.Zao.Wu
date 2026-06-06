from l5_phase3_sample_factory import complete_record, complete_snapshot, registry_namespace
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind, PluginRegistryConflictSeverity, PluginRegistryValidator


def test_plain_credential_and_missing_data_governance_are_conflicts():
    record = complete_record(credential_decl_ref="credential:token=realvalue", data_governance_decl_ref="")
    report = PluginRegistryValidator(validator_ref="validator:test").validate(complete_snapshot((record,)), (registry_namespace(),))
    assert any(c.kind is PluginRegistryConflictKind.CREDENTIAL_DECL_CONFLICT and c.severity is PluginRegistryConflictSeverity.P0 for c in report.conflicts)
    assert any(c.kind is PluginRegistryConflictKind.DATA_GOVERNANCE_CONFLICT for c in report.conflicts)
