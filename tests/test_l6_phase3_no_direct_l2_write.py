import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_no_direct_l2_write():
    assert L6Phase3MindQualityGateDecision(no_direct_l2_write_passed=False).allow_enter_phase4 is False
    with pytest.raises(ValueError):
        MindStateEnvelope(is_l2_fact=True)
    with pytest.raises(ValueError):
        CandidateFactProposal(writes_l2_fact=True)
