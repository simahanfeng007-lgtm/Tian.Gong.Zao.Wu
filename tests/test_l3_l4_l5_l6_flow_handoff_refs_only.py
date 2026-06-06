from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l3_orchestration import L3ToL4HandoffEnvelope, L3ToL5HandoffEnvelope, L3ToL6HandoffEnvelope


def typed(index: int, ref_type: str) -> TypedRef:
    return TypedRef(RefId(f"ref:{index:032x}"), ref_type)


def test_l3_handoff_envelopes_accept_flow_refs_only():
    flow_ref = typed(30, "orchestration_flow")
    for cls in (L3ToL4HandoffEnvelope, L3ToL5HandoffEnvelope, L3ToL6HandoffEnvelope):
        envelope = cls(envelope_ref=typed(31, "handoff"), flow_refs=(flow_ref,))
        assert envelope.flow_refs == (flow_ref,)
        assert envelope.handoff_only is True
