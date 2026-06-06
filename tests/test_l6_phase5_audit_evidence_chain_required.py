import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_audit_evidence_chain_required():
    assert GovernanceEvidenceIndex().evidence_item_refs
    assert GovernanceTraceRef().trace_is_database_write is False
    assert ResponsibilityChainRef().chain_refs
    assert TamperEvidenceHint().writes_tamper_log is False
    assert AuditCoverageHint().all_high_risk_has_evidence is True
    with pytest.raises(ValueError):
        AuditCoverageHint(all_high_risk_has_evidence=False)
