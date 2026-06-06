import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_invariant_suite_exists():
    invariants = default_l6_phase4_invariant_rules()
    affective = default_l6_phase4_affective_invariant_rules()
    assert len(invariants) >= 10
    assert len(affective) >= 10
    assert any(rule.invariant_ref == "invariant:l6_phase4_affective_projection_is_not_fact" for rule in affective)
