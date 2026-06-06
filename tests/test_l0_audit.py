import tiangong_kernel.l0_primitives.audit as module
from phase8_helpers import assert_enum_values, assert_module_dataclasses
from tiangong_kernel.l0_primitives.audit import ResponsibilityKind, AuditCoverageKind, AuditFindingKind


def test_l0_audit_objects_construct_freeze_serialize_hash_and_enum_values():
    assert_module_dataclasses(module)
    assert_enum_values(ResponsibilityKind, {'ORIGINATOR': 'originator', 'OBSERVER': 'observer'})
    assert_enum_values(AuditCoverageKind, {'INPUT': 'input', 'LIFECYCLE': 'lifecycle'})
    assert_enum_values(AuditFindingKind, {'MISSING_EVIDENCE': 'missing_evidence', 'RECOVERY_GAP': 'recovery_gap'})
