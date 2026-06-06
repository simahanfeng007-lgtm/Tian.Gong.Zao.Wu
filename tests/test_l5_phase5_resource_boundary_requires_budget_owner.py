from l5_phase5_helpers import validate_all, valid_resource
from tiangong_kernel.l5_plugin_host import PluginPhase5ConflictKind


def test_resource_boundary_requires_budget_owner():
    report = validate_all(resource_decls=(valid_resource(budget_owner_ref=""),))
    assert any(c.kind is PluginPhase5ConflictKind.RESOURCE_MISSING_BUDGET_OWNER_CONFLICT for c in report.conflicts)
