from l5_phase5_helpers import validate_all, valid_isolation
from tiangong_kernel.l5_plugin_host import PluginPhase5ConflictKind, PluginPhase5ConflictSeverity


def test_isolation_missing_boundary_and_no_live_action_are_blocking():
    report = validate_all(isolation_decls=(valid_isolation(isolation_boundary_ref="", no_live_action_ref=""),))
    kinds = {c.kind for c in report.conflicts}
    assert PluginPhase5ConflictKind.ISOLATION_MISSING_BOUNDARY_CONFLICT in kinds
    assert PluginPhase5ConflictKind.ISOLATION_MISSING_NO_LIVE_ACTION_CONFLICT in kinds
    assert report.p1_count >= 2


def test_isolation_live_locator_is_p0():
    report = validate_all(isolation_decls=(valid_isolation(sandbox_requirement_ref="file:///tmp/live"),))
    assert any(c.severity is PluginPhase5ConflictSeverity.P0 for c in report.conflicts)
