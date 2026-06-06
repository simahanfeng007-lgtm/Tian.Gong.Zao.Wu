import pytest
from tiangong_kernel.l6_plugins.adaptive_collaboration import AdaptiveArtifactBase

def test_adaptive_result_must_not_be_faked():
    assert AdaptiveArtifactBase().result_verified is False
    with pytest.raises(ValueError):
        AdaptiveArtifactBase(result_verified=True)
