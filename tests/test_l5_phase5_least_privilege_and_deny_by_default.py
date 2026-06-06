from l5_phase5_helpers import validate_all, valid_dependency
from tiangong_kernel.l5_plugin_host import PluginPhase5ConflictKind


def test_least_privilege_and_deny_by_default_are_required():
    report = validate_all(dependency_decls=(valid_dependency(least_privilege_declared=False),))
    assert any(c.kind is PluginPhase5ConflictKind.PHASE5_BOUNDARY_USED_AS_PERMISSION_GRANT_CONFLICT for c in report.conflicts)
