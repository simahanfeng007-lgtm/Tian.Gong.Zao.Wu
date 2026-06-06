from l5_phase4_helpers import valid_state_machine


def test_state_machine_has_no_current_state_or_runtime_context():
    sm = valid_state_machine()
    for name in ("current_state", "active_state", "runtime_status", "state_store", "runtime_context", "plugin_instance_ref"):
        assert not hasattr(sm, name)
