import pytest
from tiangong_kernel.l6_plugins.final_closure import FinalClosureArtifactBase

def test_no_parallel_runtime_or_agent_scheduler():
    with pytest.raises(ValueError):
        FinalClosureArtifactBase(parallel_runtime_created=True)
