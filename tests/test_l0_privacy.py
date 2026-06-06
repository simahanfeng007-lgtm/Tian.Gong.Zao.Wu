from dataclasses import FrozenInstanceError
import pytest
from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.serialization import stable_json_dumps, stable_hash

def rid(prefix: str = "ref") -> RefId:
    return RefId(f"{prefix}:" + "7" * 32)

def assert_frozen(obj):
    with pytest.raises(FrozenInstanceError):
        obj.schema_version = "x"

def assert_stable(obj):
    assert stable_json_dumps(obj) == stable_json_dumps(obj)
    assert stable_hash(obj) == stable_hash(obj)

from tiangong_kernel.l0_primitives.privacy import PrivacyRef, ConsentRef, DataClass, DataSubjectRef, ProcessingPurposeRef, RetentionPolicyRef, DataLifecycleState, AccessSensitivity, RedactionRef, AnonymizationRef

def test_privacy_objects_construct_freeze_serialize_hash_and_enum_values():
    subject = DataSubjectRef(rid())
    purpose = ProcessingPurposeRef(rid())
    retention = RetentionPolicyRef(rid())
    consent = ConsentRef(rid(), subject, purpose)
    privacy = PrivacyRef(rid(), DataClass.PERSONAL, DataLifecycleState.RETAINED, AccessSensitivity.HIGH, subject, consent, purpose, retention, RedactionRef(rid()), AnonymizationRef(rid()))
    assert DataClass.SECRET.value == "secret"
    assert DataLifecycleState.DELETION_REQUESTED.value == "deletion_requested"
    assert AccessSensitivity.UNKNOWN.value == "unknown"
    for obj in (subject, purpose, retention, consent, privacy):
        assert_frozen(obj); assert_stable(obj)
