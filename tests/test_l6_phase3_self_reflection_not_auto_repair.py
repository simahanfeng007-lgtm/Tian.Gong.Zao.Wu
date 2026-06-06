import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_self_reflection_not_apply_repair():
    assert SelfReflectionMindState().applies_repair is False
    assert SelfReflectionReport().applies_repair is False
    with pytest.raises(ValueError):
        SelfReflectionMindState(applies_repair=True)
    with pytest.raises(ValueError):
        SelfReflectionReport(applies_repair=True)
