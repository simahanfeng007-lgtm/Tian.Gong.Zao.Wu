from l5_phase5_helpers import validate_all, valid_data_governance
from tiangong_kernel.l5_plugin_host import PluginPhase5ConflictKind


def test_data_governance_requires_consent_purpose_lifecycle():
    report = validate_all(data_governance_decls=(valid_data_governance(consent_refs=(), purpose_refs=(), data_lifecycle_refs=()),))
    kinds = {c.kind for c in report.conflicts}
    assert PluginPhase5ConflictKind.DATA_GOVERNANCE_MISSING_CONSENT_CONFLICT in kinds
    assert PluginPhase5ConflictKind.DATA_GOVERNANCE_MISSING_PURPOSE_CONFLICT in kinds
    assert PluginPhase5ConflictKind.DATA_GOVERNANCE_MISSING_LIFECYCLE_CONFLICT in kinds
