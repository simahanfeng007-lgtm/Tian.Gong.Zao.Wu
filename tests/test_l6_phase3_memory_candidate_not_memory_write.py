import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_memory_candidate_is_not_memory_write():
    assert MemoryCandidateMindState().writes_memory is False
    assert MemoryPromotionCandidate().writes_memory is False
    with pytest.raises(ValueError):
        MemoryCandidateMindState(writes_memory=True)
    with pytest.raises(ValueError):
        MemoryRecallCandidate(injects_context=True)
