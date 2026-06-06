from l5_phase4_helpers import valid_self_healing, validate_self_healing
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind


def test_transaction_compensation_refs_are_required_but_not_executed():
    decl = valid_self_healing(transaction_ref="", compensation_ref="")
    report, _ = validate_self_healing(decls=(decl,))
    kinds = {c.kind for c in report.conflict_items}
    assert PluginRegistryConflictKind.SELF_HEALING_MISSING_TRANSACTION_CONFLICT in kinds
    assert PluginRegistryConflictKind.SELF_HEALING_MISSING_COMPENSATION_CONFLICT in kinds
    assert not hasattr(decl, "compensate")
