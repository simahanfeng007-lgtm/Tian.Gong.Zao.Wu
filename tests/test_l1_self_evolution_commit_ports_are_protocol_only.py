from __future__ import annotations

from inspect import isabstract

import pytest

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l1_ports.self_evolution_commit_ports import (
    EvolutionActivationHint,
    EvolutionCommitIntent,
    EvolutionHotSwitchBoundary,
    EvolutionPostCommitObservationIntent,
    EvolutionRollbackValidationHint,
    EvolutionTombstoneHint,
    SelfEvolutionCommitBoundaryPort,
    SelfEvolutionCommitBoundaryRequest,
    SelfEvolutionCommitBoundaryResponse,
)


def _ref(suffix: int, ref_type: str = "self_evolution") -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), ref_type)


def test_l1_self_evolution_commit_objects_are_protocol_only() -> None:
    commit = EvolutionCommitIntent(_ref(1), candidate_ref=_ref(2), human_confirmation_ref=_ref(3), boundary_permit_ref=_ref(4))
    activation = EvolutionActivationHint(_ref(5), commit_intent_ref=commit.intent_ref)
    hot_switch = EvolutionHotSwitchBoundary(_ref(6), activation_hint_ref=activation.hint_ref, rollback_anchor_ref=_ref(7))
    observation = EvolutionPostCommitObservationIntent(_ref(8), commit_intent_ref=commit.intent_ref)
    tombstone = EvolutionTombstoneHint(_ref(9), superseded_candidate_ref=_ref(10))
    rollback_validation = EvolutionRollbackValidationHint(_ref(11), rollback_ref=_ref(12), validation_refs=(_ref(13),))
    request = SelfEvolutionCommitBoundaryRequest(_ref(14), commit_intent=commit, activation_hint=activation, hot_switch_boundary=hot_switch)
    response = SelfEvolutionCommitBoundaryResponse(_ref(15), boundary_refs=(_ref(16),))

    assert commit.intent_only is True
    assert commit.applies_patch is False
    assert commit.commits_change is False
    assert commit.auto_merge is False
    assert activation.activates_runtime is False
    assert hot_switch.executes_hot_switch is False
    assert observation.samples_real_observation is False
    assert tombstone.deletes_artifact is False
    assert rollback_validation.executes_rollback is False
    assert rollback_validation.marks_success_without_validation is False
    assert request.request_only is True
    assert response.grants_commit_permission is False
    assert isabstract(SelfEvolutionCommitBoundaryPort)

    with pytest.raises(ValueError):
        EvolutionCommitIntent(_ref(17), auto_merge=True)
    with pytest.raises(ValueError):
        EvolutionHotSwitchBoundary(_ref(18), executes_hot_switch=True)
