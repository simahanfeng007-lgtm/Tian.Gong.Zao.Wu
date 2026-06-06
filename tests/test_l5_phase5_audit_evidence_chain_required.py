from l5_phase5_helpers import validate_all, valid_isolation, valid_audit_index
from tiangong_kernel.l5_plugin_host import PluginPhase5ConflictKind


def test_missing_audit_chain_field_is_p1():
    report = validate_all(isolation_decls=(valid_isolation(actor_ref=""),))
    assert any(c.kind is PluginPhase5ConflictKind.AUDIT_EVIDENCE_CHAIN_MISSING_CONFLICT for c in report.conflicts)
    assert report.p1_count >= 1


def test_audit_index_has_event_first_refs():
    index = valid_audit_index()
    assert index.isolation_event_refs
    assert index.quality_gate_event_ref
    assert index.handoff_event_ref
    assert index.audit_digest
