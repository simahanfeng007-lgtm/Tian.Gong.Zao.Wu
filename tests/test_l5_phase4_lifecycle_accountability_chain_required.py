from l5_phase4_helpers import valid_state_machine, validate_lifecycle
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind


def test_state_machine_missing_accountability_chain_fails():
    sm = valid_state_machine(actor_ref="", scope_ref="", accountability_ref="", provenance_refs=(), tamper_evidence_ref="")
    report, _ = validate_lifecycle(sm)
    assert report.p1_count >= 1
    assert any(c.kind is PluginRegistryConflictKind.RESPONSIBILITY_CHAIN_CONFLICT for c in report.conflict_items)
