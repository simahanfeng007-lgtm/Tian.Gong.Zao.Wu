import tiangong_kernel.l0_primitives.evidence as module
from phase8_helpers import assert_enum_values, assert_module_dataclasses
from tiangong_kernel.l0_primitives.evidence import EvidenceKind, EvidenceState


def test_l0_evidence_objects_construct_freeze_serialize_hash_and_enum_values():
    assert_module_dataclasses(module)
    assert_enum_values(EvidenceKind, {'EVENT_EVIDENCE': 'event_evidence', 'AUDIT_EVIDENCE': 'audit_evidence'})
    assert_enum_values(EvidenceState, {'PROPOSED': 'proposed', 'REDACTED': 'redacted'})
