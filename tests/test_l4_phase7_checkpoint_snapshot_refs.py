import pytest

from l4_phase7_builders import checkpoint_ref, phase7_ref, snapshot_ref
from tiangong_kernel.l4_action_grounding import ExecutionCheckpointRef, ExecutionSnapshotRef


def test_l4_phase7_checkpoint_and_snapshot_are_refs_only():
    checkpoint = checkpoint_ref()
    snapshot = snapshot_ref()

    assert checkpoint.ref_only is True
    assert checkpoint.creates_real_checkpoint is False
    assert checkpoint.saves_real_file is False
    assert checkpoint.persists_state is False
    assert checkpoint.writes_l2_state is False
    assert snapshot.ref_only is True
    assert snapshot.creates_real_snapshot is False
    assert snapshot.copies_sensitive_content is False
    assert snapshot.writes_persistent_storage is False
    assert snapshot.writes_l2_state is False


def test_l4_phase7_checkpoint_and_snapshot_reject_persistence_flags():
    with pytest.raises(ValueError):
        ExecutionCheckpointRef(checkpoint_ref=phase7_ref(150, "execution_checkpoint"), persists_state=True)
    with pytest.raises(ValueError):
        ExecutionSnapshotRef(snapshot_ref=phase7_ref(151, "execution_snapshot"), creates_real_snapshot=True)
