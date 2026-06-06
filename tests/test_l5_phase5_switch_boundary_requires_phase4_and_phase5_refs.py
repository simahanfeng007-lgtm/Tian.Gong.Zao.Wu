from l5_phase5_helpers import validate_all, valid_switch_boundary
from tiangong_kernel.l5_plugin_host import PluginPhase5ConflictKind


def test_switch_boundary_missing_required_refs_blocks():
    report = validate_all(switch_boundary_decls=(valid_switch_boundary(hot_switch_decl_ref="", switch_readiness_ref="", isolation_boundary_ref=""),))
    kinds = {c.kind for c in report.conflicts}
    assert PluginPhase5ConflictKind.SWITCH_BOUNDARY_MISSING_HOT_SWITCH_REF_CONFLICT in kinds
    assert PluginPhase5ConflictKind.SWITCH_BOUNDARY_MISSING_READINESS_REF_CONFLICT in kinds
    assert PluginPhase5ConflictKind.SWITCH_BOUNDARY_MISSING_ISOLATION_BOUNDARY_CONFLICT in kinds
