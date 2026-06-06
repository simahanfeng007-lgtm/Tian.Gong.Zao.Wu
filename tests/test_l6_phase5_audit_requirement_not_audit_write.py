import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_audit_requirement_not_audit_write():
    req = AuditRequirement()
    assert req.audit_store_write is False
    assert req.evidence_index_required is True
    assert GovernanceEvidenceIndex().fabricated_evidence is False
    with pytest.raises(ValueError):
        AuditRequirement(audit_store_write=True)
