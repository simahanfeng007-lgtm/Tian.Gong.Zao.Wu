import pytest
from tiangong_kernel.l6_plugins.final_closure import FinalClosureArtifactBase

def test_no_direct_file_write():
    with pytest.raises(ValueError):
        FinalClosureArtifactBase(file_written_as_plugin_action=True)
