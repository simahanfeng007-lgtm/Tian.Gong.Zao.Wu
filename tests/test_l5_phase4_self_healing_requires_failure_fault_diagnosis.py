from l5_phase4_helpers import valid_self_healing, validate_self_healing
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind


def test_self_healing_requires_failure_fault_diagnosis():
    report, _ = validate_self_healing(decls=(valid_self_healing(failure_ref="", fault_ref="", diagnosis_ref=""),))
    kinds = {c.kind for c in report.conflict_items}
    assert PluginRegistryConflictKind.SELF_HEALING_MISSING_FAILURE_REF_CONFLICT in kinds
    assert PluginRegistryConflictKind.SELF_HEALING_MISSING_FAULT_REF_CONFLICT in kinds
    assert PluginRegistryConflictKind.SELF_HEALING_MISSING_DIAGNOSIS_REF_CONFLICT in kinds
