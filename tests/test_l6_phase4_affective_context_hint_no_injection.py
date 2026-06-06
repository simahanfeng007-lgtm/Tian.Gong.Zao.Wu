import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_affective_context_hint_no_injection():
    hint = AffectiveContextModulationHint(attention_sensitivity_delta=0.2)
    assert hint.is_context_injection is False
    assert hint.bypasses_context_policy is False
    with pytest.raises(ValueError):
        AffectiveContextModulationHint(is_context_injection=True)
