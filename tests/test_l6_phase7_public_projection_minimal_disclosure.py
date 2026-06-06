import pytest
from tiangong_kernel.l6_plugins.adaptive_collaboration import AdaptivePublicProjection

def test_public_projection_minimal_disclosure():
    projection = AdaptivePublicProjection()
    assert projection.exposes_full_prompt is False
    with pytest.raises(ValueError):
        AdaptivePublicProjection(exposes_full_prompt=True)
