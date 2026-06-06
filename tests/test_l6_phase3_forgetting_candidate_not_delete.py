import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_forgetting_candidate_not_delete_and_l5_retention_protected():
    assert ForgettingCandidate().deletes_memory is False
    assert ForgettingCandidate().protected_l5_retention_respected is True
    assert MemoryRetentionExceptionHint().l5_never_forget_respected is True
    with pytest.raises(ValueError):
        ForgettingCandidate(deletes_memory=True)
    with pytest.raises(ValueError):
        ForgettingCandidateMindState(protected_l5_memory_retained=False)
