import pytest
from tiangong_kernel.l6_plugins.final_closure import L6AuditEvidenceChainIndex

def test_audit_evidence_chain_coverage():
    chain = L6AuditEvidenceChainIndex()
    assert chain.trace_coverage and chain.responsibility_coverage and chain.tamper_coverage and chain.digest_coverage
    with pytest.raises(ValueError):
        L6AuditEvidenceChainIndex(trace_coverage=False)
