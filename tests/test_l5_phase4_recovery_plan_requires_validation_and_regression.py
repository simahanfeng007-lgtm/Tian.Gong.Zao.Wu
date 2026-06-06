from l5_phase4_helpers import valid_recovery_plan, validate_self_healing
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind


def test_recovery_plan_requires_validation_and_regression():
    report, _ = validate_self_healing(plans=(valid_recovery_plan(validation_ref="", regression_ref=""),))
    kinds = {c.kind for c in report.conflict_items}
    assert PluginRegistryConflictKind.SELF_HEALING_MISSING_VALIDATION_CONFLICT in kinds
    assert PluginRegistryConflictKind.SELF_HEALING_MISSING_REGRESSION_CONFLICT in kinds
