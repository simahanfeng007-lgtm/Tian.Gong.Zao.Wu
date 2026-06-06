import pytest
from tiangong_kernel.l6_plugins.final_closure import FinalClosureArtifactBase

def test_no_direct_zip_creation_as_plugin_action():
    with pytest.raises(ValueError):
        FinalClosureArtifactBase(zip_created_as_plugin_action=True)
