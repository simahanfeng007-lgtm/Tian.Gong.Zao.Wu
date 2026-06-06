import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_seven_emotions_no_permission_bypass():
    vector = SevenEmotionSignalVector(joy=0.7)
    assert vector.expression_only is True
    assert vector.permission_bypass is False
    assert vector.tool_dispatch is False
    with pytest.raises(ValueError):
        SevenEmotionSignalVector(permission_bypass=True)
    with pytest.raises(ValueError):
        SevenEmotionSignalVector(tool_dispatch=True)
