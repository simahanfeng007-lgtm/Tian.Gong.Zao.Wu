from l5_phase5_helpers import validate_all, valid_credential
from tiangong_kernel.l5_plugin_host import PluginPhase5ConflictKind


def test_credential_missing_handle_binding_purpose_revocation_blocks():
    report = validate_all(credential_decls=(valid_credential(credential_handle_refs=(), credential_binding_refs=(), credential_purpose_refs=(), credential_revocation_ref=""),))
    kinds = {c.kind for c in report.conflicts}
    assert PluginPhase5ConflictKind.CREDENTIAL_MISSING_BINDING_CONFLICT in kinds
    assert PluginPhase5ConflictKind.CREDENTIAL_MISSING_PURPOSE_CONFLICT in kinds
    assert PluginPhase5ConflictKind.CREDENTIAL_MISSING_REVOCATION_CONFLICT in kinds
