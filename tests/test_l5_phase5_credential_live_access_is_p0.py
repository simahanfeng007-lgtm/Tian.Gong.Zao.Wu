from l5_phase5_helpers import validate_all, valid_credential
from tiangong_kernel.l5_plugin_host import PluginPhase5ConflictKind, PluginPhase5ConflictSeverity


def test_credential_secret_like_value_is_p0():
    report = validate_all(credential_decls=(valid_credential(credential_handle_refs=("sk-123456789012345",)),))
    assert any(c.kind is PluginPhase5ConflictKind.CREDENTIAL_PLAINTEXT_SECRET_CONFLICT for c in report.conflicts)
    assert any(c.severity is PluginPhase5ConflictSeverity.P0 for c in report.conflicts)
