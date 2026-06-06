from typing import get_type_hints

from tiangong_kernel.l0_primitives.decision import Decision
from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.risk import RiskView
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.state import ConstraintRef, InvariantRef, StateDeltaRef, StateSnapshotRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l1_ports.envelope import PortBoundaryContext
from tiangong_kernel.l2_state import (
    L2DeltaEntry,
    L2StateBoundary,
    L2StateDelta,
    L2StateIdentity,
    L2StateInvariant,
    L2StateMetadata,
    L2StateSnapshot,
    L2StateStatus,
)


def _field_types(cls):
    return get_type_hints(cls)


def test_l2_phase1_reuses_l0_and_l1_reference_types():
    metadata = _field_types(L2StateMetadata)
    identity = _field_types(L2StateIdentity)
    status = _field_types(L2StateStatus)
    boundary = _field_types(L2StateBoundary)
    snapshot = _field_types(L2StateSnapshot)
    delta_entry = _field_types(L2DeltaEntry)
    delta = _field_types(L2StateDelta)
    invariant = _field_types(L2StateInvariant)

    assert metadata["trace_context"] == TraceContext | None
    assert metadata["source_ref"] == TypedRef | None
    assert identity["state_ref"] is TypedRef
    assert identity["parent_ref"] == TypedRef | None
    assert identity["scope_ref"] == ScopeRef | None
    assert status["since_ref"] == TypedRef | None
    assert boundary["boundary_context"] == PortBoundaryContext | None
    assert boundary["risk_view"] == RiskView | None
    assert boundary["decision"] == Decision | None
    assert snapshot["snapshot_ref"] is StateSnapshotRef
    assert delta_entry["subject_ref"] is TypedRef
    assert delta["delta_ref"] is StateDeltaRef
    assert invariant["invariant_ref"] is InvariantRef
    assert invariant["constraint_refs"] == tuple[ConstraintRef, ...]
