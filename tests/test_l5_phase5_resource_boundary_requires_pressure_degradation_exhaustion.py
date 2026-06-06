from l5_phase5_helpers import validate_all, valid_resource
from tiangong_kernel.l5_plugin_host import PluginPhase5ConflictKind


def test_resource_boundary_requires_pressure_degradation_exhaustion():
    report = validate_all(resource_decls=(valid_resource(resource_pressure_policy_ref="", degradation_policy_ref="", exhaustion_behavior_ref=""),))
    kinds = {c.kind for c in report.conflicts}
    assert PluginPhase5ConflictKind.RESOURCE_MISSING_RESOURCE_PRESSURE_POLICY_CONFLICT in kinds
    assert PluginPhase5ConflictKind.RESOURCE_MISSING_DEGRADATION_POLICY_CONFLICT in kinds
    assert PluginPhase5ConflictKind.RESOURCE_MISSING_EXHAUSTION_BEHAVIOR_CONFLICT in kinds
