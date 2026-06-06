from l5_phase4_helpers import deep_copy, valid_mount, valid_state_machine, validate_lifecycle


def test_lifecycle_validator_does_not_modify_inputs():
    sm = valid_state_machine()
    mount = valid_mount()
    before_sm = deep_copy(sm)
    before_mount = deep_copy(mount)
    validate_lifecycle(sm, (mount,))
    assert sm == before_sm
    assert mount == before_mount
