from l5_phase4_helpers import deep_copy, valid_phase3_snapshot, valid_state_machine, validate_lifecycle


def test_phase3_snapshot_input_is_read_only_consumed():
    snapshot = valid_phase3_snapshot()
    original = deep_copy(snapshot)
    validate_lifecycle(valid_state_machine(registry_snapshot_ref=snapshot.snapshot_ref))
    assert snapshot == original
