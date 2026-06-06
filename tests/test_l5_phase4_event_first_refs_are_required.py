from l5_phase4_helpers import valid_state_machine, valid_transition, validate_lifecycle
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind


def test_transition_requires_event_refs_not_only_summary():
    sm = valid_state_machine(valid_transition(lifecycle_event_refs=()))
    report, _ = validate_lifecycle(sm)
    assert any(c.kind is PluginRegistryConflictKind.RESPONSIBILITY_CHAIN_CONFLICT for c in report.conflict_items)
