from l5_phase3_sample_factory import complete_record, complete_snapshot, registry_namespace
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind, PluginRegistryValidator


def test_forbidden_live_l6_and_legacy_patterns_are_reported_from_declaration_text_only():
    record = complete_record(summary="importlib.import_module MemoryPlugin AbilityPackage")
    report = PluginRegistryValidator(validator_ref="validator:test").validate(complete_snapshot((record,)), (registry_namespace(),))
    kinds = {c.kind for c in report.conflicts}
    assert PluginRegistryConflictKind.LIVE_ACTION_CONFLICT in kinds
    assert PluginRegistryConflictKind.L6_IMPLEMENTATION_CONFLICT in kinds
    assert PluginRegistryConflictKind.LEGACY_RUNTIME_CONFLICT in kinds
