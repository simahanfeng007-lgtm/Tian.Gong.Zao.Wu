import pytest
from tiangong_kernel.l6_plugins.product_delivery import *

def test_public_projection_minimal_disclosure():
    projection = ProductPublicProjection()
    assert projection.privacy_class is ProductPrivacyClass.PUBLIC_SUMMARY
    assert projection.exposes_full_prompt is False
    with pytest.raises(ValueError):
        ProductPublicProjection(exposes_full_prompt=True)
