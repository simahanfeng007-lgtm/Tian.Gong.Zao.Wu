from l5_phase5_helpers import validate_all, valid_resource
from tiangong_kernel.l5_plugin_host import PluginPhase5ConflictKind, PluginPhase5ConflictSeverity


def test_resource_boundary_rejects_unbounded_budget_text():
    report = validate_all(resource_decls=(valid_resource(high_permission_budget_policy_ref="policy:unlimited"),))
    assert any(c.kind is PluginPhase5ConflictKind.RESOURCE_UNBOUNDED_BUDGET_DECLARED_CONFLICT for c in report.conflicts)
    assert any(c.severity is PluginPhase5ConflictSeverity.P0 for c in report.conflicts)
