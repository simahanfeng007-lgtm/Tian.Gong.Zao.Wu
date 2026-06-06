import pytest

from tiangong_kernel.l2_state import AuditObservationKind, AuditObservationState, AuditObservationStatus
from tests.test_l2_phase5_cross_phase_references import build_phase5_chain, identity, status


def test_l2_phase5_audit_observation_expresses_audit_kinds_and_statuses():
    for audit_kind in (
        AuditObservationKind.RUN_AUDIT,
        AuditObservationKind.TASK_AUDIT,
        AuditObservationKind.SKILL_AUDIT,
        AuditObservationKind.TOOL_INTENT_AUDIT,
        AuditObservationKind.ACTION_AUDIT,
        AuditObservationKind.EFFECT_AUDIT,
        AuditObservationKind.BOUNDARY_AUDIT,
        AuditObservationKind.SECURITY_AUDIT,
    ):
        state = AuditObservationState(identity=identity(250), status=status(), audit_kind=audit_kind)
        assert state.audit_kind is audit_kind

    for audit_status in (
        AuditObservationStatus.NOTED,
        AuditObservationStatus.LINKED,
        AuditObservationStatus.REDACTED,
        AuditObservationStatus.INCOMPLETE,
        AuditObservationStatus.CONFLICTED,
    ):
        state = AuditObservationState(identity=identity(251), status=status(), audit_status=audit_status)
        assert state.audit_status is audit_status


def test_l2_phase5_audit_observation_records_refs_without_writes_or_signatures():
    objects = build_phase5_chain()
    audit = objects["audit"]

    assert audit.frame_state_refs == (objects["frame"].identity.state_ref,)
    assert audit.event_stream_state_refs == (objects["stream"].identity.state_ref,)
    assert audit.metric_state_refs == (objects["metric"].identity.state_ref,)
    assert audit.audit_payload_ref is not None
    assert audit.related_boundary_state_refs == (objects["phase4"]["boundary_check"].identity.state_ref,)
    assert audit.related_security_state_refs == (objects["phase4"]["security"].identity.state_ref,)
    assert not hasattr(audit, "write_audit")
    assert not hasattr(audit, "sign")
    assert not hasattr(audit, "verify")


def test_l2_phase5_audit_observation_rejects_long_raw_audit_summary():
    with pytest.raises(ValueError):
        AuditObservationState(identity=identity(252), status=status(), audit_summary="x" * 513)
