import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_affective_memory_hint_no_write():
    hint = AffectiveMemoryWeightHint(salience_delta=0.2)
    assert hint.is_memory_update_proposal is False
    assert hint.writes_memory is False
    with pytest.raises(ValueError):
        AffectiveMemoryWeightHint(is_memory_update_proposal=True)
    with pytest.raises(ValueError):
        AffectiveMemoryWeightHint(force_recall=True)
