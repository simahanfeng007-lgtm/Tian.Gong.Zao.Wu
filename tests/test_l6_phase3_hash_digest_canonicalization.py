import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_hash_digest_canonicalization_is_stable_and_sensitive_to_changes():
    a = MindScoreVector(belief=0.7)
    b = MindScoreVector(belief=0.7)
    c = MindScoreVector(belief=0.8)
    assert a.digest == b.digest
    assert a.digest != c.digest
    assert len(a.digest) == 64
