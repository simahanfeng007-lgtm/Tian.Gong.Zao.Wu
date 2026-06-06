import pytest

from tiangong_kernel.l5_plugin_host import L5FinalAuditIndex, L5FinalAuditIndexBuilder, L5FinalPublicProjection, L5L6HandoffFreeze
from tests.l5_phase8_factories import passing_quality_gate


def test_l5_phase8_final_audit_index_event_first_refs_required():
    index = L5FinalAuditIndexBuilder().make_index(quality_gate=passing_quality_gate(), projection=L5FinalPublicProjection(), handoff=L5L6HandoffFreeze())
    assert index.event_refs
    assert index.evidence_refs
    assert index.provenance_refs
    assert index.audit_digest
    assert index.self_healing_refs
    assert index.recovery_plan_refs
    assert index.self_evolution_requirement_refs
    assert index.memory_forgetting_refs


@pytest.mark.parametrize(
    "kwargs",
    (
        {"event_refs": ()},
        {"evidence_refs": ()},
        {"provenance_refs": ()},
        {"accountability_ref": ""},
        {"tamper_evidence_ref": ""},
    ),
)
def test_l5_phase8_final_audit_index_rejects_missing_event_evidence_refs(kwargs):
    with pytest.raises(ValueError):
        L5FinalAuditIndex(**kwargs)
