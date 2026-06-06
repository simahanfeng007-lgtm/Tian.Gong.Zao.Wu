import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_affective_reentry_goes_through_l3_l5():
    envelope = AffectiveReentryEnvelope()
    assert envelope.l3_review_required is True
    assert envelope.l5_review_required is True
    assert envelope.l2_direct_write is False
    assert envelope.memory_direct_write is False
    with pytest.raises(ValueError):
        AffectiveReentryEnvelope(l3_review_required=False)
    with pytest.raises(ValueError):
        AffectiveReentryEnvelope(memory_direct_write=True)
