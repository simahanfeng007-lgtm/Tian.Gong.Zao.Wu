from __future__ import annotations

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l1_ports.memory_governance_ports import ForgettingGovernanceRequest
from tiangong_kernel.l2_state.memory_forgetting_state import MemoryDeletionLinkState
from tiangong_kernel.l2_state.state_identity import L2StateIdentity, L2StateKind
from tiangong_kernel.l2_state.state_status import L2StateStatus, L2StateStatusKind
from tiangong_kernel.l3_orchestration.forgetting_service_request import DeletionTombstoneAdvice, ForgettingServiceRequest, ForgettingServiceRequestRef
from tiangong_kernel.l4_execution.l4_to_l6_forgetting_sink_requirement import L4ToL6ForgettingSinkRequirement


def _ref(suffix: int, ref_type: str = "memory_forgetting_chain") -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), ref_type)


def test_memory_forgetting_governance_chain_refs_only() -> None:
    forgetting_ref = _ref(1, "forgetting")
    deletion_ref = _ref(2, "deletion")
    tombstone_ref = _ref(3, "tombstone")
    audit_ref = _ref(4, "audit")
    evidence_ref = _ref(5, "evidence")

    l1_request = ForgettingGovernanceRequest(_ref(6), forgetting_refs=(forgetting_ref,), deletion_refs=(deletion_ref,), tombstone_refs=(tombstone_ref,), audit_refs=(audit_ref,))
    l2_state = MemoryDeletionLinkState(
        identity=L2StateIdentity(_ref(7, "l2_state"), L2StateKind.MEMORY_CONTEXT),
        status=L2StateStatus(L2StateStatusKind.DECLARED),
        forgetting_ref=forgetting_ref,
        deletion_ref=deletion_ref,
        tombstone_ref=tombstone_ref,
        audit_ref=audit_ref,
        evidence_ref=evidence_ref,
    )
    l3_request = ForgettingServiceRequest(
        ForgettingServiceRequestRef(_ref(8)),
        deletion_tombstone_advices=(DeletionTombstoneAdvice(_ref(9), forgetting_ref=forgetting_ref, deletion_ref=deletion_ref, tombstone_ref=tombstone_ref, audit_ref=audit_ref),),
    )
    l4_requirement = L4ToL6ForgettingSinkRequirement(
        _ref(10),
        forgetting_intent_refs=l1_request.forgetting_refs,
        deletion_refs=(l2_state.deletion_ref,),
        tombstone_refs=(l2_state.tombstone_ref,),
        audit_refs=(l2_state.audit_ref,),
    )

    assert l1_request.request_only is True
    assert l2_state.ref_only is True
    assert l2_state.deletes_memory is False
    assert l3_request.request_only is True
    assert l4_requirement.requirement_only is True
    assert l4_requirement.executes_forgetting is False
