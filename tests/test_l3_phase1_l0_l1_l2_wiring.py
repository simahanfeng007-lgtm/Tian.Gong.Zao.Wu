from l3_phase1_builders import build_l3_objects, port_request
from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l1_ports import PortRequest
from tiangong_kernel.l2_state import AffectiveColorState, DynamicWeightState, MathFeatureState, RuntimeSliceProjectionState


def test_l3_phase1_references_l0_l1_l2_without_owning_external_capability():
    objects = build_l3_objects()
    request = objects["request"]
    result = objects["result"]
    math_input = objects["math_input"]
    assert isinstance(request.inbound_request, PortRequest)
    assert isinstance(port_request(), PortRequest)
    assert isinstance(result.core_result, CoreResult)
    assert isinstance(result.recommendation_refs[0], TypedRef)
    assert isinstance(math_input.math_features[0], MathFeatureState)
    assert isinstance(math_input.math_features[0].identity.state_ref, TypedRef)
    assert isinstance(math_input.affective_input.affective_color, AffectiveColorState)
    assert isinstance(math_input.dynamic_drive_input.dynamic_weights[0], DynamicWeightState)
    assert isinstance(math_input.runtime_slice_projection, RuntimeSliceProjectionState)
    assert math_input.runtime_slice_projection.math_state_ref is not None
