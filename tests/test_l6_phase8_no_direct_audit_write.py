import pytest
from tiangong_kernel.l6_plugins.final_closure import FinalClosureArtifactBase

def test_no_direct_audit_write():
    with pytest.raises(ValueError):
        FinalClosureArtifactBase(audit_written=True)
