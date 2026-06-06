import pytest
from tiangong_kernel.l6_plugins.final_closure import FinalClosureArtifactBase

def test_no_direct_test_execution_as_plugin_action():
    with pytest.raises(ValueError):
        FinalClosureArtifactBase(test_executed_as_plugin_action=True)
