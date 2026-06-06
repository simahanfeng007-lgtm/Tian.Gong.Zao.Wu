from tiangong_kernel.l6_plugins.adaptive_collaboration import AdaptivePublicProjection
import pytest

def test_no_raw_secret_or_provider_locator():
    with pytest.raises(ValueError):
        AdaptivePublicProjection(public_summary='secret=abc')
    with pytest.raises(ValueError):
        AdaptivePublicProjection(public_summary='https://provider.example')
