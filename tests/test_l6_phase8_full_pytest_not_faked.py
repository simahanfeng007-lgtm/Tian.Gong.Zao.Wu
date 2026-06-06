import pytest
from tiangong_kernel.l6_plugins.final_closure import L6FullPytestEvidenceRef, FinalClosureArtifactBase

def test_full_pytest_not_faked():
    assert L6FullPytestEvidenceRef().faked is False
    with pytest.raises(ValueError):
        L6FullPytestEvidenceRef(faked=True)
    with pytest.raises(ValueError):
        FinalClosureArtifactBase(result_faked=True)
