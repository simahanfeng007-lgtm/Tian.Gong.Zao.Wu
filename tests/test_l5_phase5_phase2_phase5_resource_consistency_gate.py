from l5_phase5_helpers import validate_all, valid_resource
from tiangong_kernel.l5_plugin_host import PluginPhase5ConflictKind


def test_missing_phase2_resource_decl_blocks_consistency():
    report = validate_all(resource_decls=(valid_resource(phase2_resource_decl_ref=""),))
    assert any(c.kind is PluginPhase5ConflictKind.RESOURCE_PHASE2_DECL_MISSING_CONFLICT for c in report.conflicts)
