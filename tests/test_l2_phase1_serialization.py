from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps
from tiangong_kernel.l0_primitives.state import ConstraintRef, InvariantRef, StateDeltaRef, StateSnapshotRef
from tiangong_kernel.l1_ports.envelope import PortBoundaryContext
from tiangong_kernel.l2_state import (
    L2BoundaryStatusKind,
    L2DeltaEntry,
    L2DeltaKind,
    L2InvariantCheck,
    L2InvariantStatusKind,
    L2SnapshotSummary,
    L2StateBoundary,
    L2StateDelta,
    L2StateIdentity,
    L2StateInvariant,
    L2StateKind,
    L2StateMetadata,
    L2StateRecord,
    L2StateSnapshot,
    L2StateStatus,
    L2StateStatusKind,
)


def _ref(value: str) -> RefId:
    return RefId(value)


def _typed(value: str, ref_type: str = "l2_state") -> TypedRef:
    return TypedRef(_ref(value), ref_type)


def test_l2_phase1_objects_are_stably_serializable_and_hashable():
    state_ref = _typed("ref:00000000000000000000000000000001")
    evidence_ref = _typed("ref:00000000000000000000000000000002", "evidence")
    scope_ref = ScopeRef(_ref("scope:00000000000000000000000000000003"))
    identity = L2StateIdentity(
        state_ref=state_ref,
        kind=L2StateKind.BASE,
        scope_ref=scope_ref,
    )
    status = L2StateStatus(
        kind=L2StateStatusKind.DECLARED,
        reason="phase1 baseline",
        evidence_refs=(evidence_ref,),
    )
    metadata = L2StateMetadata(
        source_ref=state_ref,
        evidence_refs=(evidence_ref,),
        audit_refs=(evidence_ref,),
    )
    boundary = L2StateBoundary(
        status=L2BoundaryStatusKind.PASSED,
        boundary_context=PortBoundaryContext(alternative_paths=("manual_review",)),
        evidence_refs=(evidence_ref,),
    )
    record = L2StateRecord(
        identity=identity,
        status=status,
        metadata=metadata,
        boundary=boundary,
    )
    snapshot = L2StateSnapshot(
        snapshot_ref=StateSnapshotRef(_ref("snapshot:00000000000000000000000000000004")),
        state_refs=(state_ref,),
        summary=L2SnapshotSummary(total_states=1, active_states=0),
        metadata=metadata,
    )
    delta_entry = L2DeltaEntry(
        subject_ref=state_ref,
        kind=L2DeltaKind.CREATED,
        after_ref=state_ref,
        evidence_refs=(evidence_ref,),
    )
    delta = L2StateDelta(
        delta_ref=StateDeltaRef(_ref("delta:00000000000000000000000000000005")),
        entries=(delta_entry,),
        metadata=metadata,
    )
    invariant = L2StateInvariant(
        invariant_ref=InvariantRef(_ref("invariant:00000000000000000000000000000006")),
        constraint_refs=(ConstraintRef(_ref("constraint:00000000000000000000000000000007")),),
        subject_refs=(state_ref,),
        description="phase1 invariant declaration",
    )
    check = L2InvariantCheck(
        invariant_ref=invariant.invariant_ref,
        status=L2InvariantStatusKind.DECLARED,
        evidence_refs=(evidence_ref,),
    )

    for item in (identity, status, metadata, boundary, record, snapshot, delta_entry, delta, invariant, check):
        payload = stable_json_dumps(item)
        digest = stable_hash(item)
        assert '"schema_version":"0.1"' in payload
        assert len(digest) == 64
