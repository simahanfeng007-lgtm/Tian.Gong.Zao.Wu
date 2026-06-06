import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_no_direct_memory_write():
    assert L6Phase3MindQualityGateDecision(no_direct_memory_write_passed=False).allow_enter_phase4 is False
    assert MemoryPromotionCandidate().writes_memory is False
    assert MemoryRecallCandidate().writes_memory is False
    with pytest.raises(ValueError):
        MemoryPromotionCandidate(writes_memory=True)
