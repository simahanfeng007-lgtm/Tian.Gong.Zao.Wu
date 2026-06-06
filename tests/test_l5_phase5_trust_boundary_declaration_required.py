from l5_phase5_helpers import validate_all, valid_trust_boundary
from tiangong_kernel.l5_plugin_host import PluginPhase5ConflictKind


def test_trust_boundary_missing_core_refs_blocks():
    report = validate_all(trust_boundary_decls=(valid_trust_boundary(host_boundary_ref="", plugin_boundary_ref="", data_boundary_refs=()),))
    kinds = {c.kind for c in report.conflicts}
    assert PluginPhase5ConflictKind.TRUST_BOUNDARY_MISSING_HOST_BOUNDARY_CONFLICT in kinds
    assert PluginPhase5ConflictKind.TRUST_BOUNDARY_MISSING_PLUGIN_BOUNDARY_CONFLICT in kinds
    assert PluginPhase5ConflictKind.TRUST_BOUNDARY_MISSING_DATA_BOUNDARY_CONFLICT in kinds
