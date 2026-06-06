from l5_phase2_sample_factory import mutable_manifest_namespace, quality_gate
from tiangong_kernel.l5_plugin_host import PluginResourceDeclaration


def test_resource_decl_missing_budget_owner_and_scopes_blocks_manifest():
    manifest = mutable_manifest_namespace()
    manifest.resource_decl = PluginResourceDeclaration(cost_budget_ref="budget:cost", rate_limit_ref="rate:one", quota_ref="quota:one")
    report = quality_gate().evaluate(manifest)
    fields = {issue.field_path for issue in report.issues}
    assert "resource_decl.budget_owner_ref" in fields
    assert "resource_decl.run_budget_scope_ref" in fields
    assert "resource_decl.goal_budget_scope_ref" in fields
    assert "resource_decl.actor_budget_scope_ref" in fields
