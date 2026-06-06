from dataclasses import FrozenInstanceError

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.learning import (
    AdaptationKind,
    AdaptationRef,
    AdaptationState,
    EvolutionCommitRef,
    EvolutionKind,
    EvolutionRef,
    EvolutionRollbackRef,
    EvolutionState,
    ExperienceRef,
    ImprovementAssessmentRef,
    ImprovementProposalRef,
    LearningKind,
    LearningRef,
    LearningState,
    LessonRef,
)
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps


def rid(prefix: str = "ref") -> RefId:
    return RefId(f"{prefix}:" + "4" * 32)


def tref(kind: str = "learning") -> TypedRef:
    return TypedRef(rid("ref"), kind)


def test_learning_objects_construct_immutable_and_stable():
    experience = ExperienceRef(rid(), origin_ref=tref("event"))
    lesson = LessonRef(rid(), experience_ref=experience)
    proposal = ImprovementProposalRef(rid(), subject_ref=tref("subject"))
    assessment = ImprovementAssessmentRef(rid(), proposal_ref=proposal, decision_ref=tref("decision"))
    commit = EvolutionCommitRef(rid(), evolution_ref=tref("evolution"))
    rollback = EvolutionRollbackRef(rid(), evolution_ref=tref("evolution"), reason_ref=tref("reason"))
    learning = LearningRef(rid(), kind=LearningKind.FAILURE_LEARNING, state=LearningState.ACTIVE, experience_ref=experience, lesson_ref=lesson)
    adaptation = AdaptationRef(rid(), kind=AdaptationKind.CONTEXT_ADAPTATION, state=AdaptationState.APPROVED, subject_ref=tref("context"))
    evolution = EvolutionRef(
        rid(),
        kind=EvolutionKind.MEMORY_EVOLUTION,
        state=EvolutionState.PROPOSED,
        proposal_ref=proposal,
        assessment_ref=assessment,
        commit_ref=commit,
        rollback_ref=rollback,
    )
    for obj in (learning, adaptation, evolution):
        assert stable_hash(obj) == stable_hash(obj)
        assert "schema_version" in stable_json_dumps(obj)
    try:
        learning.state = LearningState.ARCHIVED
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("LearningRef allowed mutation")


def test_learning_enum_values_are_stable():
    assert LearningKind.EPISODIC_LEARNING.value == "episodic_learning"
    assert LearningKind.SEMANTIC_LEARNING.value == "semantic_learning"
    assert LearningKind.PROCEDURAL_LEARNING.value == "procedural_learning"
    assert LearningKind.FAILURE_LEARNING.value == "failure_learning"
    assert LearningKind.FEEDBACK_LEARNING.value == "feedback_learning"
    assert LearningKind.PREFERENCE_LEARNING.value == "preference_learning"
    assert LearningKind.POLICY_LEARNING.value == "policy_learning"
    assert LearningKind.UNKNOWN.value == "unknown"
    assert AdaptationKind.CONTEXT_ADAPTATION.value == "context_adaptation"
    assert AdaptationKind.PLAN_ADAPTATION.value == "plan_adaptation"
    assert AdaptationKind.POLICY_ADAPTATION.value == "policy_adaptation"
    assert AdaptationKind.RESOURCE_ADAPTATION.value == "resource_adaptation"
    assert AdaptationKind.MEMORY_ADAPTATION.value == "memory_adaptation"
    assert AdaptationKind.RETRIEVAL_ADAPTATION.value == "retrieval_adaptation"
    assert AdaptationKind.CONTROL_MODE_ADAPTATION.value == "control_mode_adaptation"
    assert AdaptationKind.UNKNOWN.value == "unknown"
    assert EvolutionKind.MEMORY_EVOLUTION.value == "memory_evolution"
    assert EvolutionKind.SKILL_EVOLUTION.value == "skill_evolution"
    assert EvolutionKind.TOOL_EVOLUTION.value == "tool_evolution"
    assert EvolutionKind.PLUGIN_EVOLUTION.value == "plugin_evolution"
    assert EvolutionKind.POLICY_EVOLUTION.value == "policy_evolution"
    assert EvolutionKind.CONTRACT_EVOLUTION.value == "contract_evolution"
    assert EvolutionKind.SCHEMA_EVOLUTION.value == "schema_evolution"
    assert EvolutionKind.CODE_EVOLUTION.value == "code_evolution"
    assert EvolutionKind.ARCHITECTURE_EVOLUTION.value == "architecture_evolution"
    assert EvolutionKind.UNKNOWN.value == "unknown"
    for enum_cls in (LearningState, AdaptationState, EvolutionState):
        assert enum_cls.PROPOSED.value == "proposed"
        assert enum_cls.ASSESSING.value == "assessing"
        assert enum_cls.APPROVED.value == "approved"
        assert enum_cls.ACTIVE.value == "active"
        assert enum_cls.COMMITTED.value == "committed"
        assert enum_cls.REJECTED.value == "rejected"
        assert enum_cls.ROLLED_BACK.value == "rolled_back"
        assert enum_cls.QUARANTINED.value == "quarantined"
        assert enum_cls.ARCHIVED.value == "archived"
        assert enum_cls.UNKNOWN.value == "unknown"
