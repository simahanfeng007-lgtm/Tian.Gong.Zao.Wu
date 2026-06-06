import pytest

from l4_phase6_builders import action_ref, audit_ref, evidence_ref, observation_ref, phase6_ref, trace_ref
from tiangong_kernel.l4_action_grounding import ExecutionAuditRef, ExecutionEvidenceRef, ExecutionObservationRef, ExecutionTraceRef


def test_l4_phase6_observation_evidence_audit_trace_are_refs_only():
    obs = observation_ref()
    evidence = evidence_ref()
    audit = audit_ref()
    trace = trace_ref()

    assert obs.samples_real_observation is False
    assert obs.reads_real_screen is False
    assert evidence.stores_real_evidence is False
    assert evidence.copies_sensitive_content is False
    assert audit.writes_real_audit is False
    assert audit.writes_audit_store is False
    assert trace.creates_legacy_trace is False
    assert trace.writes_trace_store is False


def test_l4_phase6_refs_reject_real_sampling_storage_and_audit_write():
    with pytest.raises(ValueError):
        ExecutionObservationRef(observation_ref=phase6_ref(110, "observation"), action_ref=action_ref(), samples_real_observation=True)
    with pytest.raises(ValueError):
        ExecutionEvidenceRef(evidence_ref=phase6_ref(111, "evidence"), action_ref=action_ref(), stores_real_evidence=True)
    with pytest.raises(ValueError):
        ExecutionAuditRef(audit_ref=phase6_ref(112, "audit"), action_ref=action_ref(), writes_audit_store=True)
    with pytest.raises(ValueError):
        ExecutionTraceRef(trace_ref=phase6_ref(113, "trace"), action_ref=action_ref(), creates_legacy_trace=True)
