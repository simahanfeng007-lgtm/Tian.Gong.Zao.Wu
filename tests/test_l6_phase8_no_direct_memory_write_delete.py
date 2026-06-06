import pytest
from tiangong_kernel.l6_plugins.final_closure import FinalClosureArtifactBase

def test_no_direct_memory_write_delete():
    with pytest.raises(ValueError):
        FinalClosureArtifactBase(memory_written=True)
    with pytest.raises(ValueError):
        FinalClosureArtifactBase(memory_deleted=True)
