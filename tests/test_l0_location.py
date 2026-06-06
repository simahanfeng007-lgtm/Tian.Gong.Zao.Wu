from dataclasses import FrozenInstanceError
import pytest
from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.serialization import stable_json_dumps, stable_hash

def rid(prefix: str = "ref") -> RefId:
    return RefId(f"{prefix}:" + "9" * 32)

def assert_frozen(obj):
    with pytest.raises(FrozenInstanceError):
        obj.schema_version = "x"

def assert_stable(obj):
    assert stable_json_dumps(obj) == stable_json_dumps(obj)
    assert stable_hash(obj) == stable_hash(obj)

from tiangong_kernel.l0_primitives.location import LocationKind, LocationRef, LocationState, AddressKind, AddressRef, URIKind, URIRef, LocatorKind, LocatorRef, ResolutionHintRef

def test_location_objects_construct_freeze_serialize_hash_and_enum_values():
    loc = LocationRef(rid(), LocationKind.ARTIFACT, LocationState.KNOWN)
    addr = AddressRef(rid(), AddressKind.URI, loc)
    uri = URIRef(rid(), URIKind.HTTPS, addr)
    locator = LocatorRef(rid(), LocatorKind.CONTENT_ADDRESSABLE, uri)
    hint = ResolutionHintRef(rid(), locator)
    assert LocationKind.SANDBOX.value == "sandbox"
    assert AddressKind.CONTENT_ADDRESS.value == "content_address"
    assert URIKind.CUSTOM.value == "custom"
    assert LocatorKind.TEMPORARY.value == "temporary"
    for obj in (loc, addr, uri, locator, hint):
        assert_frozen(obj); assert_stable(obj)
