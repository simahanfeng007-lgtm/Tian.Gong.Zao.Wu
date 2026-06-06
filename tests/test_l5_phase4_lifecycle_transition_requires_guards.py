from l5_phase4_helpers import valid_state_machine, valid_transition, validate_lifecycle
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind


def test_transition_missing_guard_blocks_quality():
    sm = valid_state_machine(valid_transition(guard_refs=()))
    report, _ = validate_lifecycle(sm)
    assert report.p1_count >= 1
    assert any(c.kind is PluginRegistryConflictKind.LIFECYCLE_MISSING_GUARD_CONFLICT for c in report.conflict_items)


def test_transition_missing_policy_audit_evidence_blocks_quality():
    sm = valid_state_machine(valid_transition(required_policy_refs=(), audit_event_ref="", required_evidence_refs=()))
    report, _ = validate_lifecycle(sm)
    kinds = {c.kind for c in report.conflict_items}
    assert PluginRegistryConflictKind.LIFECYCLE_MISSING_POLICY_CONFLICT in kinds
    assert PluginRegistryConflictKind.LIFECYCLE_MISSING_AUDIT_CONFLICT in kinds
    assert PluginRegistryConflictKind.LIFECYCLE_MISSING_EVIDENCE_CONFLICT in kinds
