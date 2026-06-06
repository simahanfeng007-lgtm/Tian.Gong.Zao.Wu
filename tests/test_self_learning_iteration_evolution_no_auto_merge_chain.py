from __future__ import annotations

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l1_ports.self_evolution_commit_ports import EvolutionCommitIntent
from tiangong_kernel.l2_state.self_evolution_commit_state import EvolutionCommitState
from tiangong_kernel.l2_state.state_identity import L2StateIdentity, L2StateKind
from tiangong_kernel.l2_state.state_status import L2StateStatus, L2StateStatusKind
from tiangong_kernel.l3_orchestration.self_evolution_commit_flow import CandidateValidatedToCommitAdvice
from tiangong_kernel.l4_execution.l4_to_l5_self_evolution_requirement import L4ToL5SelfEvolutionBoundaryRequirement
from tiangong_kernel.l4_execution.l4_to_l6_self_evolution_requirement import L4ToL6EvolutionCommitRequirement


def _ref(suffix: int, ref_type: str = "self_evolution") -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), ref_type)


def test_self_evolution_commit_requires_l5_permit_and_human_confirmation_when_required() -> None:
    candidate_ref = _ref(1, "candidate")
    commit_intent = EvolutionCommitIntent(_ref(2), candidate_ref=candidate_ref, validation_refs=(_ref(3),), human_confirmation_ref=_ref(4), boundary_permit_ref=_ref(5))
    state = EvolutionCommitState(
        identity=L2StateIdentity(_ref(6, "l2_state"), L2StateKind.CANDIDATE),
        status=L2StateStatus(L2StateStatusKind.DECLARED),
        candidate_ref=candidate_ref,
        commit_intent_ref=commit_intent.intent_ref,
        human_confirmation_ref=commit_intent.human_confirmation_ref,
        boundary_ref=commit_intent.boundary_permit_ref,
    )
    advice = CandidateValidatedToCommitAdvice(_ref(7), candidate_ref=candidate_ref, validation_refs=commit_intent.validation_refs, commit_intent_ref=commit_intent.intent_ref)
    l5_boundary = L4ToL5SelfEvolutionBoundaryRequirement(_ref(8), candidate_refs=(candidate_ref,), validation_refs=commit_intent.validation_refs)
    l6_commit = L4ToL6EvolutionCommitRequirement(_ref(9), commit_intent_refs=(commit_intent.intent_ref,))

    assert commit_intent.auto_merge is False
    assert commit_intent.applies_patch is False
    assert state.requires_l5_permit is True
    assert state.no_patch_apply is True
    assert advice.requires_human_confirmation is True
    assert advice.grants_permission is False
    assert l5_boundary.requires_human_confirmation_when_required is True
    assert l5_boundary.grants_permission is False
    assert l6_commit.commits_change is False
    assert l6_commit.hot_switches is False
