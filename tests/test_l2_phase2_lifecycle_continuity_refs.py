from tiangong_kernel.l1_ports.state_continuity_ports import (
    CheckpointReference,
    ContinuityEvidence,
    StateRecoveryHint,
)
from tests.test_l2_phase2_serialization import build_phase2_objects


def test_l2_phase2_lifecycle_and_continuity_reference_chain():
    agent, run, task, _, lifecycle, continuity, checkpoint_continuity, recovery_continuity = build_phase2_objects()

    assert lifecycle.target_state_ref == run.identity.state_ref
    assert lifecycle.previous_state_ref == agent.identity.state_ref
    assert lifecycle.next_expected_state_ref == task.identity.state_ref
    assert continuity.snapshot_ref == run.snapshot_ref
    assert continuity.checkpoint_ref == run.checkpoint_ref
    assert continuity.recovery_point_ref == run.recovery_point_ref
    assert checkpoint_continuity.continuity == continuity
    assert isinstance(checkpoint_continuity.checkpoint_reference, CheckpointReference)
    assert recovery_continuity.continuity == continuity
    assert isinstance(recovery_continuity.recovery_hint, StateRecoveryHint)
    assert isinstance(recovery_continuity.continuity_evidence, ContinuityEvidence)
    assert recovery_continuity.recoverable is True
