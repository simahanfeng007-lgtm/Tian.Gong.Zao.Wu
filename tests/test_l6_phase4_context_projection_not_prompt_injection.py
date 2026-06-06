import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_context_projection_not_prompt_injection():
    projection = ContextContinuityProjection(continuity_score=0.8)
    assert projection.reentry_required is True
    assert projection.is_prompt_injection is False
    with pytest.raises(ValueError):
        ContextContinuityProjection(is_prompt_injection=True)
