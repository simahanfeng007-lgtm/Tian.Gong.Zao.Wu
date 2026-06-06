from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l3_orchestration import HumanApprovalFlow


def typed(index: int, ref_type: str) -> TypedRef:
    return TypedRef(RefId(f"ref:{index:032x}"), ref_type)


def test_l3_human_approval_flow_wait_resume_expire_deny_refs_only():
    flow = HumanApprovalFlow(
        approval_request_refs=(typed(10, "approval_request"),),
        wait_refs=(typed(11, "wait_ref"),),
        resume_refs=(typed(12, "resume_ref"),),
        expiration_refs=(typed(13, "expiration_ref"),),
        denial_refs=(typed(14, "denial_ref"),),
    )
    assert flow.confirmation_ticket_issued is False
    assert flow.no_decision is True
    assert flow.no_execution is True
    assert flow.wait_refs and flow.resume_refs and flow.expiration_refs and flow.denial_refs
