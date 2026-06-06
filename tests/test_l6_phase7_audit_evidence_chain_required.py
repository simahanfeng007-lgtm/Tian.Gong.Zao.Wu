from tiangong_kernel.l6_plugins.adaptive_collaboration import LearningNeedReviewRequest

def test_audit_evidence_chain_required():
    req = LearningNeedReviewRequest()
    assert req.evidence_refs
    assert req.trace_ref.startswith('ref:')
    assert req.responsibility_chain_ref.startswith('responsibility:')
