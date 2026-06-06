import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_context_projection_not_prompt_injection():
    assert ContextMindState().context_is_prompt_injection is False
    assert ContextProjection().is_prompt_injection is False
    assert ContextSafetyProjection().injects_prompt is False
    with pytest.raises(ValueError):
        ContextMindState(context_is_prompt_injection=True)
    with pytest.raises(ValueError):
        ContextProjection(is_prompt_injection=True)
    with pytest.raises(ValueError):
        ContextSafetyProjection(injects_prompt=True)
