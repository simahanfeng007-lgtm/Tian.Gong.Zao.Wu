from l5_phase4_helpers import migration_transition, valid_state_machine, validate_lifecycle
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind


def test_migration_requires_migration_compatibility_and_breaking_change_refs():
    sm = valid_state_machine(migration_transition(migration_ref="", compatibility_check_ref="", breaking_change_check_ref="", breaking_change_policy_ref=""))
    report, _ = validate_lifecycle(sm)
    kinds = {c.kind for c in report.conflict_items}
    assert PluginRegistryConflictKind.LIFECYCLE_MISSING_MIGRATION_REF_CONFLICT in kinds
    assert PluginRegistryConflictKind.LIFECYCLE_MISSING_COMPATIBILITY_CHECK_CONFLICT in kinds
    assert PluginRegistryConflictKind.LIFECYCLE_MISSING_BREAKING_CHANGE_CHECK_CONFLICT in kinds
