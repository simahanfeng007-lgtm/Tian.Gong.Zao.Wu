import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_cognitive_group_is_not_runtime():
    architecture = CognitiveContinuityGroupArchitecture()
    assert architecture.cognitive_group_is_not_runtime is True
    assert architecture.l3_reentry_required is True
    assert architecture.l5_review_required is True
    with pytest.raises(ValueError):
        CognitiveContinuityGroupArchitecture(creates_parallel_runtime=True)
