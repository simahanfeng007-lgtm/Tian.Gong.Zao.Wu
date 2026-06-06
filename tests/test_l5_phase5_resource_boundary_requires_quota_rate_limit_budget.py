from l5_phase5_helpers import validate_all, valid_resource
from tiangong_kernel.l5_plugin_host import PluginPhase5ConflictKind


def test_resource_boundary_missing_budget_refs_blocks():
    report = validate_all(resource_decls=(valid_resource(quota_policy_ref="", rate_limit_policy_ref="", budget_ledger_ref="", cost_policy_ref=""),))
    kinds = {c.kind for c in report.conflicts}
    assert PluginPhase5ConflictKind.RESOURCE_MISSING_QUOTA_POLICY_CONFLICT in kinds
    assert PluginPhase5ConflictKind.RESOURCE_MISSING_RATE_LIMIT_POLICY_CONFLICT in kinds
    assert PluginPhase5ConflictKind.RESOURCE_MISSING_BUDGET_LEDGER_CONFLICT in kinds
    assert PluginPhase5ConflictKind.RESOURCE_MISSING_COST_POLICY_CONFLICT in kinds
