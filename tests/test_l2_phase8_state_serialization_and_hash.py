from dataclasses import replace

from l2_phase8_builders import build_all_phase8_objects, build_catalog_closure_objects, identity, status, typed
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps
from tiangong_kernel.l0_primitives.state import StateSnapshotRef
from tiangong_kernel.l2_state import (
    L2SnapshotSummary,
    L2StateCatalog,
    L2StateKind,
    L2StateSnapshot,
    ModelVisibleStateProjection,
    ProjectionStatus,
)


def test_l2_phase8_objects_are_stably_serializable_and_hashable():
    for name, item in build_all_phase8_objects().items():
        payload = stable_json_dumps(item)
        digest = stable_hash(item)
        assert isinstance(payload, str), name
        assert isinstance(digest, str), name
        assert len(digest) == 64, name
        assert stable_hash(item) == digest, name


def test_l2_phase8_stable_hash_changes_when_projection_fact_changes():
    first = ModelVisibleStateProjection(
        identity=identity(950, L2StateKind.PROJECTION),
        status=status(),
        projection_id=typed(951, "projection"),
        hidden_reason_summary="first",
        projection_status=ProjectionStatus.PARTIAL,
    )
    second = replace(first, hidden_reason_summary="second")
    assert stable_hash(first) != stable_hash(second)


def test_l2_phase8_closure_catalog_can_join_existing_snapshot_fact_model():
    catalog = build_catalog_closure_objects()["state_catalog"]
    snapshot = L2StateSnapshot(
        snapshot_ref=StateSnapshotRef(typed(960, "snapshot").ref_id),
        state_refs=(catalog.identity.state_ref,),
        summary=L2SnapshotSummary(total_states=1, active_states=1),
    )
    assert isinstance(catalog, L2StateCatalog)
    assert stable_hash(snapshot)
    assert catalog.identity.state_ref in snapshot.state_refs
