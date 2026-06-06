import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_hash_digest_canonicalization():
    a = GovernanceReviewRequest()
    b = GovernanceReviewRequest()
    assert a.digest == b.digest
    assert len(a.digest) == 64
    assert len(L6Phase5GovernanceQualityGateDecision(full_pytest_passed_for_freeze=True).digest) == 64
