from l5_phase5_helpers import validate_all, valid_capability_token
from tiangong_kernel.l5_plugin_host import PluginPhase5ConflictKind


def test_capability_token_missing_core_refs_blocks():
    report = validate_all(capability_token_decls=(valid_capability_token(token_scope_refs=(), token_lease_ref="", token_expiry_ref="", token_revocation_ref=""),))
    kinds = {c.kind for c in report.conflicts}
    assert PluginPhase5ConflictKind.CAPABILITY_TOKEN_MISSING_SCOPE_CONFLICT in kinds
    assert PluginPhase5ConflictKind.CAPABILITY_TOKEN_MISSING_LEASE_CONFLICT in kinds
    assert PluginPhase5ConflictKind.CAPABILITY_TOKEN_MISSING_EXPIRY_CONFLICT in kinds
    assert PluginPhase5ConflictKind.CAPABILITY_TOKEN_MISSING_REVOCATION_CONFLICT in kinds
