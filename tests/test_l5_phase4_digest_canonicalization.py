from l5_phase4_helpers import valid_state_machine, valid_transition


def test_lifecycle_digest_is_stable_for_same_semantics():
    sm1 = valid_state_machine(valid_transition())
    sm2 = valid_state_machine(valid_transition())
    assert sm1.state_machine_digest == sm2.state_machine_digest


def test_lifecycle_digest_changes_on_key_declaration_change():
    sm1 = valid_state_machine(valid_transition())
    sm2 = valid_state_machine(valid_transition(trigger_ref="trigger:other"))
    assert sm1.state_machine_digest != sm2.state_machine_digest
