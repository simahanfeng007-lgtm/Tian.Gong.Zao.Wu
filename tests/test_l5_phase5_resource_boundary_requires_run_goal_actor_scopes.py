from l5_phase5_helpers import validate_all, valid_resource
from tiangong_kernel.l5_plugin_host import PluginPhase5ConflictKind


def test_resource_boundary_requires_run_goal_actor_scopes():
    report = validate_all(resource_decls=(valid_resource(run_budget_scope_ref="", goal_budget_scope_ref="", actor_budget_scope_ref=""),))
    kinds = {c.kind for c in report.conflicts}
    assert PluginPhase5ConflictKind.RESOURCE_MISSING_RUN_BUDGET_SCOPE_CONFLICT in kinds
    assert PluginPhase5ConflictKind.RESOURCE_MISSING_GOAL_BUDGET_SCOPE_CONFLICT in kinds
    assert PluginPhase5ConflictKind.RESOURCE_MISSING_ACTOR_BUDGET_SCOPE_CONFLICT in kinds
