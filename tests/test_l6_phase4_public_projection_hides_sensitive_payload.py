import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_public_projection_hides_sensitive_payload():
    public = CognitivePublicProjection()
    assert public.contains_full_prompt is False
    assert public.contains_real_path is False
    assert public.contains_provider_locator is False
    assert public.contains_credential_material is False
    assert public.contains_execution_plan is False
    assert any(flag == "redact:full_private_memory" for flag in public.redaction_flags)
