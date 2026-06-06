from l5_phase4_helpers import hot_switch_transition


def test_hot_switch_transition_digest_is_deterministic():
    a = hot_switch_transition()
    b = hot_switch_transition()
    assert a.transition_digest == b.transition_digest
    c = hot_switch_transition(switch_readiness_ref="switch_ready:other")
    assert a.transition_digest != c.transition_digest
