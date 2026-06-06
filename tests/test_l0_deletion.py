from dataclasses import FrozenInstanceError, fields

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps
from tiangong_kernel.l0_primitives.time import TimeRange, Timestamp


def rid(prefix: str = "ref") -> RefId:
    return RefId(f"{prefix}:" + "1" * 32)


def tref(kind: str = "sample") -> TypedRef:
    return TypedRef(rid("ref"), kind)


def assert_value_object(obj):
    dumped = stable_json_dumps(obj)
    digest = stable_hash(obj)
    assert isinstance(dumped, str)
    assert isinstance(digest, str)
    assert len(digest) == 64
    field_name = fields(obj)[0].name
    try:
        setattr(obj, field_name, getattr(obj, field_name))
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(f"{type(obj).__name__} allowed mutation")

from tiangong_kernel.l0_primitives.deletion import (
    AnonymizationRef,
    CryptoErasureRef,
    DeletionEvidenceRef,
    DeletionKind,
    DeletionRef,
    DeletionState,
    ErasureKind,
    ErasureRef,
    ErasureState,
    RedactionRef,
    RetentionExceptionRef,
    TombstoneKind,
    TombstoneRef,
    TombstoneState,
)


def test_deletion_objects_construct_and_serialize():
    deletion = DeletionRef(rid(), DeletionKind.USER_REQUESTED, DeletionState.REQUESTED, tref("content"))
    erasure = ErasureRef(rid(), ErasureKind.LOGICAL_DELETE, ErasureState.APPROVED, deletion)
    tombstone = TombstoneRef(rid(), TombstoneKind.DELETED_OBJECT, TombstoneState.COMPLETED, tref("content"))
    redaction = RedactionRef(rid(), tref("content"))
    anonymization = AnonymizationRef(rid(), tref("subject"))
    crypto = CryptoErasureRef(rid(), tref("key"))
    exception = RetentionExceptionRef(rid(), tref("reason"))
    evidence = DeletionEvidenceRef(rid(), "approval", (tref("event"),))
    for obj in (deletion, erasure, tombstone, redaction, anonymization, crypto, exception, evidence):
        assert_value_object(obj)


def test_deletion_enum_values_are_stable():
    assert [item.value for item in DeletionKind] == ["user_requested", "retention_expired", "privacy_required", "safety_required", "security_required", "system_cleanup", "superseded", "duplicate", "corrupted", "unknown"]
    assert [item.value for item in ErasureKind] == ["logical_delete", "physical_delete", "cryptographic_erasure", "redaction", "anonymization", "suppression", "tombstone_only", "unknown"]
    expected = ["requested", "approved", "scheduled", "in_progress", "completed", "blocked", "exception_recorded", "failed", "verified", "archived", "unknown"]
    assert [item.value for item in DeletionState] == expected
    assert [item.value for item in ErasureState] == expected
    assert [item.value for item in TombstoneState] == expected
    assert [item.value for item in TombstoneKind] == ["deleted_object", "redacted_content", "anonymized_subject", "suppressed_record", "crypto_erased", "unknown"]
