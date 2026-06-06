from tiangong_kernel.l6_plugins.product_delivery import *

def test_audit_evidence_chain_required():
    gate = L6Phase6ProductDeliveryQualityGateDecision()
    seed = ProductSpecSeedCandidate()
    assert gate.evidence_index_refs
    assert gate.audit_ref.startswith('audit:')
    assert seed.trace_ref.startswith('ref:')
    assert seed.responsibility_chain_ref.startswith('responsibility:')
    assert seed.tamper_evidence_ref.startswith('evidence:')
