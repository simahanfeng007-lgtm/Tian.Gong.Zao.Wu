import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_audit_evidence_chain_required():
    output = ContextContinuityProjection()
    envelope = CognitiveReentryEnvelope()
    assert output.evidence_refs
    assert output.audit_ref.startswith("audit:")
    assert output.responsibility_chain_ref.startswith("responsibility:")
    assert envelope.evidence_refs
    assert envelope.audit_ref.startswith("audit:")
