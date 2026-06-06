from l5_phase5_helpers import validate_all, valid_resource
from tiangong_kernel.l5_plugin_host import PluginPhase5ConflictKind


def test_resource_boundary_rejects_live_locator():
    report = validate_all(resource_decls=(valid_resource(budget_ledger_ref="postgres://ledger/live"),))
    assert any(c.kind is PluginPhase5ConflictKind.RESOURCE_LIVE_ALLOCATION_CONFLICT for c in report.conflicts)
