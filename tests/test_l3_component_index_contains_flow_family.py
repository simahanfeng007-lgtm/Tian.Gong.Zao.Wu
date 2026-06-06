from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l3_orchestration import OrchestrationComponentIndex, OrchestrationIndexKind, OrchestrationObjectFamilyIndex


def typed(index: int, ref_type: str) -> TypedRef:
    return TypedRef(RefId(f"ref:{index:032x}"), ref_type)


def test_l3_component_index_can_represent_flow_family():
    component_index = OrchestrationComponentIndex(
        index_ref=typed(40, "l3_component_index"),
        component_names=("foundation", "flow", "closure"),
    )
    family_index = OrchestrationObjectFamilyIndex(
        index_ref=typed(41, "l3_object_family_index"),
        object_family_names=("flow",),
        representative_object_names=("CanonicalRunLoopFlowBundle", "EffectRequestFlow"),
    )
    assert "flow" in component_index.component_names
    assert "flow" in family_index.object_family_names
    assert OrchestrationIndexKind.FLOW.value == "flow"
