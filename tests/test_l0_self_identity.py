from dataclasses import FrozenInstanceError, is_dataclass

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.self_identity import (
    AffiliationRef,
    BoundaryRef,
    ContinuityRef,
    IdentityRef,
    OwnershipRef,
    SelfRef,
)
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps, to_primitive


def _ref(prefix: str, char: str) -> RefId:
    return RefId(f"{prefix}:" + char * 32)


def test_self_identity_objects_are_l0_immutable_refs():
    self_ref = SelfRef(_ref("self", "1"), label="core-self")
    identity = IdentityRef(_ref("identity", "2"), self_ref=self_ref, identity_domain="kernel")
    subject = TypedRef(identity.value, "identity")
    previous = TypedRef(_ref("identity", "3"), "identity")
    continuity = ContinuityRef(_ref("continuity", "4"), subject, previous, "version_continuity")
    boundary = BoundaryRef(_ref("boundary", "5"), subject, "identity_boundary")
    owner = TypedRef(self_ref.value, "self")
    obj = TypedRef(_ref("artifact", "6"), "artifact")
    ownership = OwnershipRef(_ref("ownership", "7"), owner, obj, "declared")
    affiliation = AffiliationRef(_ref("affiliation", "8"), subject, TypedRef(_ref("scope", "9"), "scope"), "member_of")

    payload = (self_ref, identity, continuity, boundary, ownership, affiliation)
    assert all(is_dataclass(item) for item in payload)
    assert to_primitive(identity)["identity_domain"] == "kernel"
    assert to_primitive(continuity)["continuity_kind"] == "version_continuity"
    assert stable_json_dumps(payload) == stable_json_dumps(payload)
    assert stable_hash(payload) == stable_hash(payload)


def test_self_ref_is_frozen():
    item = SelfRef(_ref("self", "a"))
    try:
        item.label = "changed"
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("SelfRef allowed mutation")
