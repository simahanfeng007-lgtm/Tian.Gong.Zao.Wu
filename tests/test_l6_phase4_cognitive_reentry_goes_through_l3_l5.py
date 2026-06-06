import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_cognitive_reentry_goes_through_l3_l5():
    envelope = CognitiveReentryEnvelope()
    assert envelope.l3_review_required is True
    assert envelope.l5_review_required is True
    assert envelope.l2_direct_write is False
    assert envelope.permission_granted is False
    with pytest.raises(ValueError):
        CognitiveReentryEnvelope(l5_review_required=False)
    with pytest.raises(ValueError):
        CognitiveReentryEnvelope(tool_direct_dispatch=True)
