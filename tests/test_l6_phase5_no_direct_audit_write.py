import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_no_direct_audit_write_declared():
    assert AuditRequirement().audit_store_write is False
    with pytest.raises(ValueError):
        GovernanceControlPluginDeclaration(plugin_ref='l6_phase5:bad_audit', plugin_kind=GovernancePluginKind.AUDIT_EVIDENCE, summary='bad', writes_audit_store=True)
