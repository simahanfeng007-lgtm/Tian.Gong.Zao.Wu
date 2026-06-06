from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps
from tiangong_kernel.l2_state import (
    L2_STATE_SCHEMA_VERSION,
    L2StateIdentity,
    L2StateKind,
    L2StateMetadata,
    L2StateRecord,
    L2StateStatus,
)


def test_l2_phase2_keeps_phase1_exports_and_serialization_compatible():
    state_ref = TypedRef(RefId("ref:00000000000000000000000000000001"), "l2_state")
    identity = L2StateIdentity(state_ref=state_ref, kind=L2StateKind.BASE)
    status = L2StateStatus(reason="phase1 compatibility")
    record = L2StateRecord(
        identity=identity,
        status=status,
        metadata=L2StateMetadata(source_ref=state_ref),
    )

    assert L2_STATE_SCHEMA_VERSION == "0.1"
    assert stable_json_dumps(record) == stable_json_dumps(record)
    assert len(stable_hash(record)) == 64
