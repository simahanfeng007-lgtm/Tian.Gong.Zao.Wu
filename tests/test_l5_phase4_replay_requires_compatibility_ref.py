from l5_phase4_helpers import replay_transition, valid_state_machine, validate_lifecycle
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind


def test_replay_requires_compatibility_ref():
    sm = valid_state_machine(replay_transition(replay_compatibility_ref=""))
    report, _ = validate_lifecycle(sm)
    assert any(c.kind is PluginRegistryConflictKind.LIFECYCLE_MISSING_REPLAY_COMPATIBILITY_CONFLICT for c in report.conflict_items)
