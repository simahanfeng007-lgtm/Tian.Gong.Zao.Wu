import pytest
from tiangong_kernel.l6_plugins.final_closure import FinalClosureArtifactBase

def test_no_raw_secret_or_provider_locator():
    with pytest.raises(ValueError):
        FinalClosureArtifactBase(credential_accessed=True)
