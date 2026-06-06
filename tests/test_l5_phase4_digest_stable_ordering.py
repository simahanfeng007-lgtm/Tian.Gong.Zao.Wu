from l5_phase4_helpers import hot_switch_transition, valid_state_machine, valid_transition


def test_digest_changes_with_transition_content_not_object_identity():
    a = valid_state_machine(valid_transition(), hot_switch_transition())
    b = valid_state_machine(valid_transition(), hot_switch_transition())
    c = valid_state_machine(hot_switch_transition(), valid_transition())
    assert a.state_machine_digest == b.state_machine_digest
    assert a.state_machine_digest != c.state_machine_digest
