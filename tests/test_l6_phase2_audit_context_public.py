import pytest

from tiangong_kernel.l6_plugins.common import (
    BeliefRequirement,
    ContextBeliefWorldHandoffEnvelope,
    ContextRequirement,
    ContextView,
    L6AuditTraceEnvelope,
    L6PublicProjection,
    WorldRequirement,
)


def test_audit_trace_envelope_requires_evidence_responsibility_and_tamper_chain():
    audit = L6AuditTraceEnvelope()
    assert audit.evidence_chain_complete is True
    assert audit.writes_audit_record is False
    assert audit.stores_evidence_blob is False
    assert audit.authorizes_execution is False
    with pytest.raises(ValueError):
        L6AuditTraceEnvelope(writes_audit_record=True)
    with pytest.raises(ValueError):
        L6AuditTraceEnvelope(stores_evidence_blob=True)
    with pytest.raises(ValueError):
        L6AuditTraceEnvelope(authorizes_execution=True)


def test_context_belief_world_requirements_are_requirement_only():
    assert ContextRequirement().requirement_only is True
    assert BeliefRequirement().writes_belief_fact is False
    assert WorldRequirement().writes_world_fact is False
    with pytest.raises(ValueError):
        ContextRequirement(injects_prompt=True)
    with pytest.raises(ValueError):
        BeliefRequirement(writes_belief_fact=True)
    with pytest.raises(ValueError):
        WorldRequirement(writes_world_fact=True)


def test_context_view_and_context_belief_world_handoff_are_not_prompt_or_l2_write():
    assert ContextView().prompt_injection_allowed is False
    assert ContextBeliefWorldHandoffEnvelope().direct_context_injection is False
    with pytest.raises(ValueError):
        ContextView(prompt_injection_allowed=True)
    with pytest.raises(ValueError):
        ContextBeliefWorldHandoffEnvelope(writes_l2_state_fact=True)
    with pytest.raises(ValueError):
        ContextBeliefWorldHandoffEnvelope(direct_context_injection=True)


def test_public_projection_safety_rejects_secret_endpoint_and_execution_markers():
    assert L6PublicProjection().contains_raw_credential is False
    assert L6PublicProjection().contains_external_endpoint is False
    with pytest.raises(ValueError):
        L6PublicProjection(status_summary="api_key=plain")
    with pytest.raises(ValueError):
        L6PublicProjection(status_summary="https://api.example.invalid")
    with pytest.raises(ValueError):
        L6PublicProjection(status_summary="subprocess shell")
