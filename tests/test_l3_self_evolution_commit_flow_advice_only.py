from __future__ import annotations

import pytest

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l3_orchestration.self_evolution_commit_flow import (
    CandidateValidatedToCommitAdvice,
    EvolutionActivationAdvice,
    EvolutionCommitFlowAdvice,
    EvolutionRollbackAfterActivationAdvice,
    HotSwitchGuardAdvice,
    PostCommitObservationAdvice,
    TombstoneMigrationAdvice,
)


def _ref(suffix: int, ref_type: str = "self_evolution") -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), ref_type)


def test_l3_self_evolution_commit_advices_never_execute() -> None:
    advices = (
        CandidateValidatedToCommitAdvice(_ref(1), candidate_ref=_ref(2), requires_human_confirmation=True),
        EvolutionCommitFlowAdvice(_ref(3), boundary_refs=(_ref(4),)),
        EvolutionActivationAdvice(_ref(5), activation_hint_ref=_ref(6)),
        HotSwitchGuardAdvice(_ref(7), rollback_anchor_ref=_ref(8)),
        PostCommitObservationAdvice(_ref(9), observation_requirement_refs=(_ref(10),)),
        EvolutionRollbackAfterActivationAdvice(_ref(11), rollback_validation_refs=(_ref(12),)),
        TombstoneMigrationAdvice(_ref(13), tombstone_ref=_ref(14)),
    )

    for advice in advices:
        assert advice.advisory_only is True
        assert advice.ref_only is True
        assert advice.no_patch_generation is True
        assert advice.no_patch_apply is True
        assert advice.no_auto_merge is True
        assert advice.no_hot_switch is True
        assert advice.no_real_rollback is True
        assert advice.grants_permission is False

    with pytest.raises(ValueError):
        EvolutionCommitFlowAdvice(_ref(15), grants_permission=True)
