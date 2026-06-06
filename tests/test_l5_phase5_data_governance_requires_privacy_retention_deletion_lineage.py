from l5_phase5_helpers import validate_all, valid_data_governance
from tiangong_kernel.l5_plugin_host import PluginPhase5ConflictKind


def test_data_governance_missing_core_refs_blocks():
    report = validate_all(data_governance_decls=(valid_data_governance(privacy_boundary_ref="", retention_policy_ref="", deletion_policy_ref="", lineage_ref=""),))
    kinds = {c.kind for c in report.conflicts}
    assert PluginPhase5ConflictKind.DATA_GOVERNANCE_MISSING_PRIVACY_BOUNDARY_CONFLICT in kinds
    assert PluginPhase5ConflictKind.DATA_GOVERNANCE_MISSING_RETENTION_POLICY_CONFLICT in kinds
    assert PluginPhase5ConflictKind.DATA_GOVERNANCE_MISSING_DELETION_POLICY_CONFLICT in kinds
    assert PluginPhase5ConflictKind.DATA_GOVERNANCE_MISSING_LINEAGE_CONFLICT in kinds
