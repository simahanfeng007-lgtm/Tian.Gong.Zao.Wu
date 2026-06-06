from __future__ import annotations

import pytest

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l4_execution.l4_to_l5_self_evolution_requirement import (
    L4ToL5SelfEvolutionBoundaryRequirement,
    L4ToL5SelfEvolutionPermitRequirement,
)
from tiangong_kernel.l4_execution.l4_to_l6_self_evolution_requirement import (
    L4ToL6EvolutionCommitRequirement,
    L4ToL6EvolutionValidationRequirement,
    L4ToL6PostCommitObservationRequirement,
    L4ToL6SelfLearningSinkRequirement,
)


def _ref(suffix: int, ref_type: str = "self_evolution") -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), ref_type)


def test_l4_self_evolution_requirements_do_not_execute_or_grant() -> None:
    boundary = L4ToL5SelfEvolutionBoundaryRequirement(_ref(1), candidate_refs=(_ref(2),), validation_refs=(_ref(3),))
    permit = L4ToL5SelfEvolutionPermitRequirement(_ref(4), commit_intent_refs=(_ref(5),))
    learning = L4ToL6SelfLearningSinkRequirement(_ref(6), learning_signal_refs=(_ref(7),))
    validation = L4ToL6EvolutionValidationRequirement(_ref(8), validation_refs=(_ref(9),))
    commit = L4ToL6EvolutionCommitRequirement(_ref(10), commit_intent_refs=(_ref(11),))
    observation = L4ToL6PostCommitObservationRequirement(_ref(12), observation_requirement_refs=(_ref(13),))

    assert boundary.requirement_only is True
    assert boundary.grants_permission is False
    assert boundary.applies_patch is False
    assert boundary.hot_switches is False
    assert boundary.requires_human_confirmation_when_required is True
    assert permit.grants_commit_permission is False
    assert permit.grants_hot_switch_permission is False
    assert permit.grants_rollback_permission is False
    assert learning.implements_learning_system is False
    assert validation.runs_validation is False
    assert commit.commits_change is False
    assert commit.hot_switches is False
    assert observation.samples_real_observation is False
    assert observation.writes_l2_state is False

    with pytest.raises(ValueError):
        L4ToL6EvolutionCommitRequirement(_ref(14), applies_patch=True)
