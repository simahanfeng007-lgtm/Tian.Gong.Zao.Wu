from l5_phase3_sample_factory import complete_record, complete_snapshot, registry_namespace
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind, PluginRegistryConflictSeverity, PluginRegistryValidator


def test_incomparable_version_without_compatibility_is_p3_not_semver_parser():
    record = complete_record(plugin_version_text="latest", compatibility_decl_ref="")
    report = PluginRegistryValidator(validator_ref="validator:test").validate(complete_snapshot((record,)), (registry_namespace(),))
    assert any(c.kind is PluginRegistryConflictKind.PLUGIN_VERSION_CONFLICT and c.severity is PluginRegistryConflictSeverity.P3 for c in report.conflicts)
