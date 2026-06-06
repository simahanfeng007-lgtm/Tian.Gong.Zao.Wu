from dataclasses import FrozenInstanceError
from l5_phase4_helpers import valid_state_machine, valid_transition
from tiangong_kernel.l5_plugin_host import PluginLifecycleStateMachine


def test_lifecycle_state_machine_is_frozen_and_has_no_runtime_state():
    sm = valid_state_machine()
    assert isinstance(sm, PluginLifecycleStateMachine)
    assert not hasattr(sm, "current_state")
    assert not hasattr(sm, "runtime_status")
    try:
        sm.lifecycle_version = "changed"
        assert False, "frozen dataclass should reject mutation"
    except FrozenInstanceError:
        assert True


def test_lifecycle_state_machine_has_digest_and_transitions_are_declarations():
    sm = valid_state_machine(valid_transition())
    assert sm.state_machine_digest
    assert sm.transition_rules[0].side_effect_free_declared is True
