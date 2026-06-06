from l5_phase4_helpers import valid_recovery_plan, validate_self_healing
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind


def test_recovery_plan_requires_checkpoint_and_recovery_point():
    report, _ = validate_self_healing(plans=(valid_recovery_plan(checkpoint_ref="", recovery_point_ref=""),))
    kinds = {c.kind for c in report.conflict_items}
    assert PluginRegistryConflictKind.SELF_HEALING_MISSING_CHECKPOINT_CONFLICT in kinds
    assert PluginRegistryConflictKind.SELF_HEALING_MISSING_RECOVERY_POINT_CONFLICT in kinds
