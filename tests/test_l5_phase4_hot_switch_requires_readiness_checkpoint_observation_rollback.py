from l5_phase4_helpers import hot_switch_transition, valid_state_machine, validate_lifecycle
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind


def test_hot_switch_requires_readiness_checkpoint_observation_rollback_refs():
    sm = valid_state_machine(hot_switch_transition(switch_readiness_ref="", pre_switch_checkpoint_ref="", post_switch_observation_ref="", switch_rollback_route_ref=""))
    report, _ = validate_lifecycle(sm)
    kinds = {c.kind for c in report.conflict_items}
    assert PluginRegistryConflictKind.LIFECYCLE_MISSING_SWITCH_READINESS_CONFLICT in kinds
    assert PluginRegistryConflictKind.LIFECYCLE_MISSING_PRE_SWITCH_CHECKPOINT_CONFLICT in kinds
    assert PluginRegistryConflictKind.LIFECYCLE_MISSING_POST_SWITCH_OBSERVATION_CONFLICT in kinds
    assert PluginRegistryConflictKind.LIFECYCLE_MISSING_SWITCH_ROLLBACK_ROUTE_CONFLICT in kinds
