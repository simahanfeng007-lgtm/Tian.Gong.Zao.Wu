from dataclasses import FrozenInstanceError, fields, is_dataclass
from enum import Enum
import inspect

import pytest

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l2_state import (
    CandidateBoundaryState,
    CandidateBoundaryStatus,
    CandidateEvidenceState,
    CandidateKind,
    CandidateLifecycleState,
    CandidateLifecycleStatus,
    CandidateRefState,
    CandidateSourceKind,
    CandidateSourceState,
    ChangeImpactState,
    ChangeImpactStatus,
    ChangeIntentState,
    ChangeKind,
    ChangePatchRefState,
    ChangeReviewState,
    ChangeReviewStatus,
    ChangeReversibilityState,
    ChangeReversibilityStatus,
    EvolutionBoundaryLabel,
    EvolutionBoundaryState,
    EvolutionCandidateState,
    EvolutionCandidateStatus,
    EvolutionContinuityState,
    EvolutionContinuityStatus,
    EvolutionDecisionHintState,
    EvolutionEvidenceState,
    EvolutionIntentKind,
    EvolutionIntentState,
    EvolutionRollbackHintState,
    IterationCandidateState,
    IterationCandidateStatus,
    IterationEvidenceState,
    IterationPatchIntentState,
    IterationReviewState,
    IterationReviewStatus,
    IterationRollbackHintState,
    IterationTargetKind,
    L2StateIdentity,
    L2StateKind,
    L2StateStatus,
    L2StateStatusKind,
)


def ref(prefix: str, index: int) -> RefId:
    return RefId(f"{prefix}:{index:032x}")


def typed(index: int, ref_type: str) -> TypedRef:
    return TypedRef(ref("phase7", index), ref_type)


def identity(index: int, kind: L2StateKind = L2StateKind.CANDIDATE) -> L2StateIdentity:
    return L2StateIdentity(state_ref=typed(index, kind.value), kind=kind)


def status() -> L2StateStatus:
    return L2StateStatus(kind=L2StateStatusKind.DECLARED, reason="phase7 fixture")


def build_candidate_change_iteration_evolution_objects():
    candidate_ref = typed(10, "candidate")
    target_ref = typed(11, "skill")
    evidence_ref = typed(12, "evidence")
    validation_ref = typed(13, "validation")
    change_ref = typed(20, "change")
    iteration_ref = typed(30, "iteration_candidate")
    evolution_intent_ref = typed(40, "evolution_intent")
    evolution_candidate_ref = typed(41, "evolution_candidate")
    continuity_ref = typed(42, "evolution_continuity")

    return {
        "candidate_ref": CandidateRefState(
            identity=identity(100),
            status=status(),
            candidate_ref=candidate_ref,
            candidate_kind=CandidateKind.LEARNING,
            subject_ref=target_ref,
            source_ref=typed(14, "model_feedback"),
            source_kind=CandidateSourceKind.MODEL_FEEDBACK,
            summary="learning candidate from model feedback",
            priority=0.8,
            lifecycle_status=CandidateLifecycleStatus.RECORDED,
        ),
        "candidate_source": CandidateSourceState(
            identity=identity(101),
            status=status(),
            source_state_ref=typed(15, "candidate_source"),
            candidate_ref=candidate_ref,
            source_kind=CandidateSourceKind.MODEL_REFLECTION,
            source_refs=(typed(16, "model_reflection"),),
            reason_summary="reflection indicated a persistent gap",
            evidence_refs=(evidence_ref,),
        ),
        "candidate_evidence": CandidateEvidenceState(
            identity=identity(102),
            status=status(),
            evidence_state_ref=typed(17, "candidate_evidence"),
            candidate_ref=candidate_ref,
            evidence_refs=(evidence_ref,),
            validation_refs=(validation_ref,),
            completeness_score=0.7,
        ),
        "candidate_boundary": CandidateBoundaryState(
            identity=identity(103),
            status=status(),
            boundary_state_ref=typed(18, "candidate_boundary"),
            candidate_ref=candidate_ref,
            boundary_label=CandidateBoundaryStatus.RECORD_ONLY,
            reason_summary="state layer can only record the candidate",
        ),
        "candidate_lifecycle": CandidateLifecycleState(
            identity=identity(104),
            status=status(),
            lifecycle_ref=typed(19, "candidate_lifecycle"),
            candidate_ref=candidate_ref,
            previous_status=CandidateLifecycleStatus.PROPOSED,
            current_status=CandidateLifecycleStatus.RECORDED,
            transition_reason="candidate recorded for downstream validation",
        ),
        "change_intent": ChangeIntentState(
            identity=identity(200, L2StateKind.CHANGE),
            status=status(),
            change_intent_ref=change_ref,
            candidate_ref=candidate_ref,
            target_ref=target_ref,
            change_kind=ChangeKind.SKILL_FLOW,
            summary="adjust skill flow description",
            evidence_refs=(evidence_ref,),
        ),
        "change_impact": ChangeImpactState(
            identity=identity(201, L2StateKind.CHANGE),
            status=status(),
            impact_ref=typed(21, "change_impact"),
            change_ref=change_ref,
            impacted_state_refs=(target_ref,),
            impacted_phase_labels=("L1", "L2"),
            impact_status=ChangeImpactStatus.CROSS_PHASE,
            risk_hint="needs_review",
        ),
        "change_reversibility": ChangeReversibilityState(
            identity=identity(202, L2StateKind.CHANGE),
            status=status(),
            reversibility_ref=typed(22, "change_reversibility"),
            change_ref=change_ref,
            recovery_point_refs=(typed(23, "recovery_point"),),
            reversibility_status=ChangeReversibilityStatus.REVERSIBLE,
        ),
        "change_patch_ref": ChangePatchRefState(
            identity=identity(203, L2StateKind.CHANGE),
            status=status(),
            patch_ref=typed(24, "patch_ref"),
            change_ref=change_ref,
            target_ref=target_ref,
            patch_hash="sha256:patch-intent-only",
            patch_summary="patch intent reference only",
            is_generated=False,
        ),
        "change_review": ChangeReviewState(
            identity=identity(204, L2StateKind.CHANGE),
            status=status(),
            review_ref=typed(25, "change_review"),
            change_ref=change_ref,
            review_status=ChangeReviewStatus.PENDING,
            evidence_refs=(evidence_ref,),
            validation_refs=(validation_ref,),
        ),
        "iteration_candidate": IterationCandidateState(
            identity=identity(300, L2StateKind.CANDIDATE),
            status=status(),
            iteration_candidate_ref=iteration_ref,
            candidate_ref=candidate_ref,
            target_kind=IterationTargetKind.SKILL_FLOW,
            target_ref=target_ref,
            source_feedback_refs=(typed(31, "model_feedback"),),
            source_learning_refs=(typed(32, "learning_signal"),),
            source_gap_refs=(typed(33, "skill_gap"),),
            summary="iteration candidate from skill gap",
            candidate_status=IterationCandidateStatus.RECORDED,
            priority=0.6,
        ),
        "iteration_patch_intent": IterationPatchIntentState(
            identity=identity(301, L2StateKind.CHANGE),
            status=status(),
            patch_intent_ref=typed(34, "iteration_patch_intent"),
            iteration_candidate_ref=iteration_ref,
            target_ref=target_ref,
            change_ref=change_ref,
            patch_intent_summary="only records that a patch may be needed",
            patch_generated=False,
        ),
        "iteration_evidence": IterationEvidenceState(
            identity=identity(302, L2StateKind.CANDIDATE),
            status=status(),
            evidence_state_ref=typed(35, "iteration_evidence"),
            iteration_candidate_ref=iteration_ref,
            evidence_refs=(evidence_ref,),
            test_refs=(typed(36, "test"),),
            verification_refs=(typed(37, "verification"),),
            completeness_score=0.5,
        ),
        "iteration_review": IterationReviewState(
            identity=identity(303, L2StateKind.CANDIDATE),
            status=status(),
            review_ref=typed(38, "iteration_review"),
            iteration_candidate_ref=iteration_ref,
            review_status=IterationReviewStatus.NEEDS_TEST_REF,
        ),
        "iteration_rollback_hint": IterationRollbackHintState(
            identity=identity(304, L2StateKind.RECOVERY),
            status=status(),
            rollback_hint_ref=typed(39, "iteration_rollback_hint"),
            iteration_candidate_ref=iteration_ref,
            recovery_point_refs=(typed(23, "recovery_point"),),
            reason_summary="iteration needs a recoverable anchor",
        ),
        "evolution_intent": EvolutionIntentState(
            identity=identity(400, L2StateKind.CANDIDATE),
            status=status(),
            evolution_intent_ref=evolution_intent_ref,
            intent_kind=EvolutionIntentKind.LONG_TERM_SKILL_GAP,
            source_ref=typed(43, "model_reflection"),
            target_ref=target_ref,
            summary="long term skill gap suggests evolution candidate",
            strength=0.7,
            evidence_refs=(evidence_ref,),
        ),
        "evolution_candidate": EvolutionCandidateState(
            identity=identity(401, L2StateKind.CANDIDATE),
            status=status(),
            evolution_candidate_ref=evolution_candidate_ref,
            candidate_ref=candidate_ref,
            intent_ref=evolution_intent_ref,
            target_ref=target_ref,
            candidate_status=EvolutionCandidateStatus.NEEDS_CONTINUITY,
            summary="candidate requires continuity statement",
            continuity_ref=continuity_ref,
        ),
        "evolution_boundary": EvolutionBoundaryState(
            identity=identity(402, L2StateKind.BOUNDARY),
            status=status(),
            boundary_state_ref=typed(44, "evolution_boundary"),
            evolution_candidate_ref=evolution_candidate_ref,
            boundary_label=EvolutionBoundaryLabel.MUST_VERIFY,
            reason_summary="evolution needs later verification",
        ),
        "evolution_evidence": EvolutionEvidenceState(
            identity=identity(403, L2StateKind.CANDIDATE),
            status=status(),
            evidence_state_ref=typed(45, "evolution_evidence"),
            evolution_candidate_ref=evolution_candidate_ref,
            evidence_refs=(evidence_ref,),
            validation_refs=(validation_ref,),
            learning_refs=(typed(46, "learning_result"),),
            completeness_score=0.4,
        ),
        "evolution_decision_hint": EvolutionDecisionHintState(
            identity=identity(404, L2StateKind.CANDIDATE),
            status=status(),
            decision_hint_ref=typed(47, "evolution_decision_hint"),
            evolution_candidate_ref=evolution_candidate_ref,
            suggested_action="needs_verification",
            reason_summary="decision hint only",
            verification_refs=(typed(37, "verification"),),
        ),
        "evolution_rollback_hint": EvolutionRollbackHintState(
            identity=identity(405, L2StateKind.RECOVERY),
            status=status(),
            rollback_hint_ref=typed(48, "evolution_rollback_hint"),
            evolution_candidate_ref=evolution_candidate_ref,
            recovery_point_refs=(typed(23, "recovery_point"),),
            reason_summary="evolution must remain reversible",
        ),
        "evolution_continuity": EvolutionContinuityState(
            identity=identity(406, L2StateKind.CANDIDATE),
            status=status(),
            continuity_ref=continuity_ref,
            evolution_candidate_ref=evolution_candidate_ref,
            continuity_status=EvolutionContinuityStatus.DECLARED,
            required_continuity_refs=(typed(49, "boundary_continuity"),),
        ),
    }


def test_l2_phase7_candidate_change_iteration_evolution_objects_are_frozen_dataclasses():
    objects = build_candidate_change_iteration_evolution_objects()
    for name, item in objects.items():
        assert is_dataclass(item), name
        assert getattr(type(item), "__slots__", None) is not None, name
        with pytest.raises(FrozenInstanceError):
            item.schema_version = "changed"  # type: ignore[misc]


def test_l2_phase7_candidate_change_iteration_evolution_public_classes_have_chinese_docstrings():
    modules = []
    for item in build_candidate_change_iteration_evolution_objects().values():
        modules.append(inspect.getmodule(type(item)))
    for module in set(modules):
        assert inspect.getdoc(module) and any("\u4e00" <= char <= "\u9fff" for char in inspect.getdoc(module))
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ != module.__name__ or cls.__name__.startswith("_") or issubclass(cls, Enum):
                continue
            assert inspect.getdoc(cls) and any("\u4e00" <= char <= "\u9fff" for char in inspect.getdoc(cls)), cls.__name__


def test_l2_phase7_candidate_change_iteration_evolution_refuse_out_of_range_scores_or_generated_patch():
    base = build_candidate_change_iteration_evolution_objects()["candidate_ref"]
    with pytest.raises(ValueError):
        CandidateRefState(identity=base.identity, status=base.status, priority=1.1)
    with pytest.raises(ValueError):
        CandidateEvidenceState(identity=base.identity, status=base.status, completeness_score=-0.1)
    with pytest.raises(ValueError):
        ChangePatchRefState(identity=base.identity, status=base.status, is_generated=True)
    with pytest.raises(ValueError):
        IterationPatchIntentState(identity=base.identity, status=base.status, patch_generated=True)
    with pytest.raises(ValueError):
        EvolutionIntentState(identity=base.identity, status=base.status, strength=1.2)


def test_l2_phase7_objects_keep_identity_status_and_schema_fields():
    for name, item in build_candidate_change_iteration_evolution_objects().items():
        field_names = {f.name for f in fields(item)}
        assert {"identity", "status", "schema_version"}.issubset(field_names), name
        assert item.schema_version == "0.1", name
