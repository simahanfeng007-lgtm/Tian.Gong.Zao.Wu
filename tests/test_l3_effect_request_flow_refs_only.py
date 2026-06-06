from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l3_orchestration import EffectRequestFlow


def typed(index: int, ref_type: str) -> TypedRef:
    return TypedRef(RefId(f"ref:{index:032x}"), ref_type)


def test_l3_effect_request_flow_is_refs_only():
    flow = EffectRequestFlow(
        effect_refs=(typed(1, "effect"),),
        side_effect_refs=(typed(2, "side_effect"),),
        audit_requirement_refs=(typed(3, "audit_requirement"),),
        boundary_request_refs=(typed(4, "boundary_request"),),
    )
    assert flow.effect_refs
    assert flow.side_effect_refs
    assert flow.audit_requirement_refs
    assert flow.boundary_request_refs
    assert flow.no_execution is True
    assert flow.no_persistence is True
