from l5_phase4_helpers import valid_self_healing, validate_self_healing
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind


def test_rollback_chain_requires_audit_and_evidence():
    report, _ = validate_self_healing(decls=(valid_self_healing(audit_decl_ref="", evidence_refs=()),))
    kinds = {c.kind for c in report.conflict_items}
    assert PluginRegistryConflictKind.SELF_HEALING_MISSING_AUDIT_CONFLICT in kinds
    assert PluginRegistryConflictKind.SELF_HEALING_MISSING_EVIDENCE_CONFLICT in kinds
