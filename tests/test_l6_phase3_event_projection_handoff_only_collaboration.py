import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_event_projection_handoff_only_collaboration():
    matrix = default_mind_interoperation_matrix()
    assert matrix.event_rule_refs
    assert matrix.state_projection_rule_refs
    assert matrix.handoff_rule_refs
    assert matrix.public_projection_rule_refs
    assert matrix.l3_l5_reschedule_refs
    assert matrix.event_projection_handoff_only_collaboration is True
    assert all(rule.direct_call_allowed is False for rule in matrix.rules)
