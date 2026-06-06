from l5_phase5_helpers import validate_all, valid_data_governance
from tiangong_kernel.l5_plugin_host import PluginPhase5ConflictKind


def test_data_governance_rejects_real_data_locator():
    report = validate_all(data_governance_decls=(valid_data_governance(lineage_ref="/var/data/customer.db"),))
    assert any(c.kind is PluginPhase5ConflictKind.DATA_GOVERNANCE_LIVE_DATA_ACCESS_CONFLICT for c in report.conflicts)
