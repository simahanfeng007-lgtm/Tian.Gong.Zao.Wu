import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_hash_digest_canonicalization():
    a = CognitiveReentryEnvelope(source_projection_refs=("projection:a", "projection:b"))
    b = CognitiveReentryEnvelope(source_projection_refs=("projection:a", "projection:b"))
    c = CognitiveReentryEnvelope(source_projection_refs=("projection:b", "projection:a"))
    assert a.digest == b.digest
    assert a.digest != c.digest
