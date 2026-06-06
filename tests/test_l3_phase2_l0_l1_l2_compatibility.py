from dataclasses import replace

from l3_phase1_builders import build_l3_objects
from l3_phase2_builders import build_l3_phase2_objects
from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l2_state import RuntimeSliceProjectionState
from tiangong_kernel.l3_orchestration import build_run_state_view_from_context, orchestration_stable_hash


def test_l3_phase2_run_view_uses_l2_projection_by_reference_only():
    phase1 = build_l3_objects()
    phase2 = build_l3_phase2_objects()
    view = phase2["run_view"]
    assert isinstance(view.runtime_slice_projection, RuntimeSliceProjectionState)
    assert isinstance(view.math_state_refs[0], TypedRef)
    assert view.math_state_refs == phase1["context"].math_state_refs
    assert view.affective_state_refs == phase1["context"].affective_state_refs
    assert view.dynamic_drive_refs == phase1["context"].dynamic_drive_refs


def test_l3_phase2_view_builder_does_not_modify_context_or_l2_state():
    phase1 = build_l3_objects()
    context = phase1["context"]
    before = orchestration_stable_hash(context)
    _view = build_run_state_view_from_context(context, build_l3_phase2_objects()["run_ref"])
    after = orchestration_stable_hash(context)
    assert before == after


def test_l3_phase2_transition_advice_does_not_mutate_l2_status_objects():
    phase1 = build_l3_objects()
    math_input = phase1["math_input"]
    feature = math_input.math_features[0]
    before = orchestration_stable_hash(feature)
    _advice = build_l3_phase2_objects()["process_advice"]
    after = orchestration_stable_hash(feature)
    assert before == after
    changed_copy = replace(feature, summary="changed copy")
    assert orchestration_stable_hash(feature) != orchestration_stable_hash(changed_copy)
