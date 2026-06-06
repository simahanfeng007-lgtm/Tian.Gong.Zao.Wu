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

from tiangong_kernel.l0_primitives.trust import TrustBoundaryRef, TrustBoundaryKind, TrustLevel, ProvenanceRef, ProvenanceKind, ResponsibilityChainRef, AttestationRef, IntegrityDigest

def test_trust_objects_construct_freeze_serialize_hash_and_enum_values():
    boundary = TrustBoundaryRef(rid(), TrustBoundaryKind.SANDBOX, TrustLevel.CONSTRAINED)
    provenance = ProvenanceRef(rid(), ProvenanceKind.USER_PROVIDED)
    chain = ResponsibilityChainRef(rid(), provenance_ref=provenance)
    attestation = AttestationRef(rid())
    digest = IntegrityDigest("a" * 64)
    assert TrustBoundaryKind.SELF_CORE.value == "self_core"
    assert TrustLevel.UNKNOWN.value == "unknown"
    assert ProvenanceKind.DERIVED.value == "derived"
    for obj in (boundary, provenance, chain, attestation, digest):
        assert_frozen(obj); assert_stable(obj)
