import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_public_projection_redaction():
    projection = AffectivePublicProjection(status=AffectivePublicStatus.PRESSURED)
    assert projection.full_affective_profile_public is False
    assert projection.full_vector_public is False
    assert any(flag == "redact:full_affective_profile" for flag in projection.redaction_flags)
    assert projection.contains_full_prompt is False
    assert projection.contains_provider_locator is False
    with pytest.raises(ValueError):
        AffectivePublicProjection(full_affective_profile_public=True)
