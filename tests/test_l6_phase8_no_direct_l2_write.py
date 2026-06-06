import pytest
from tiangong_kernel.l6_plugins.final_closure import FinalClosureArtifactBase

def test_no_direct_l2_write():
    with pytest.raises(ValueError):
        FinalClosureArtifactBase(l2_written=True)
