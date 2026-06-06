from dataclasses import FrozenInstanceError

from tiangong_kernel.l0_primitives.grant_lease import GrantKind, GrantRef, LeaseRef, LeaseStatus, PermissionWindow
from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps
from tiangong_kernel.l0_primitives.time import TemporalWindow, TimeRange, Timestamp


def test_grant_lease_objects_construction_immutability_serialization_hash_and_enum_values():
    grant = GrantRef(RefId("grant:" + "4" * 32), GrantKind.USER, TypedRef(RefId("actor:" + "5" * 32), "actor"))
    lease = LeaseRef(RefId("lease:" + "6" * 32), LeaseStatus.ACTIVE, grant)
    window = PermissionWindow(TemporalWindow(TimeRange(Timestamp(1), Timestamp(2)), "short"), lease)
    try:
        lease.status = LeaseStatus.EXPIRED
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("LeaseRef allowed mutation")
    assert '"status":"active"' in stable_json_dumps((grant, lease, window))
    assert len(stable_hash((grant, lease, window))) == 64
    assert [member.value for member in LeaseStatus] == [
        "proposed",
        "issued",
        "active",
        "expired",
        "revoked",
        "consumed",
        "suspended",
        "unknown",
    ]
