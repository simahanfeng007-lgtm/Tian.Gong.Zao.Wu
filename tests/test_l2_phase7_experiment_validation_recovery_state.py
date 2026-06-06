from dataclasses import FrozenInstanceError, fields, is_dataclass

import pytest

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l2_state import (
    CandidateValidationState,
    ExperimentComparisonState,
    ExperimentComparisonStatus,
    ExperimentDesignState,
    ExperimentIntentState,
    ExperimentKind,
    ExperimentObservationState,
    ExperimentResultState,
    ExperimentRollbackHintState,
    ExperimentStatus,
    L2StateIdentity,
    L2StateKind,
    L2StateStatus,
    L2StateStatusKind,
    RecoveryAnchorKind,
    RecoveryAnchorState,
    RecoveryLinkState,
    RecoveryOutcomeRefState,
    RecoveryOutcomeStatus,
    RecoveryReadinessState,
    RecoveryReadinessStatus,
    RecoveryValidationState,
    RollbackHintState,
    TestPlanRefState,
    ValidationIntentKind,
    ValidationIntentState,
    ValidationOutcomeRefStatus,
    ValidationReadinessStatus,
    ValidationRefState,
    VerificationRefState,
)


def ref(prefix: str, index: int) -> RefId:
    return RefId(f"{prefix}:{index:032x}")


def typed(index: int, ref_type: str) -> TypedRef:
    return TypedRef(ref("phase7", index), ref_type)


def identity(index: int, kind: L2StateKind) -> L2StateIdentity:
    return L2StateIdentity(state_ref=typed(index, kind.value), kind=kind)


def status() -> L2StateStatus:
    return L2StateStatus(kind=L2StateStatusKind.DECLARED, reason="phase7 fixture")


def build_experiment_validation_recovery_objects():
    candidate_ref = typed(10, "candidate")
    experiment_ref = typed(50, "experiment")
    design_ref = typed(51, "experiment_design")
    result_ref = typed(52, "experiment_result")
    validation_intent_ref = typed(60, "validation_intent")
    validation_ref = typed(61, "validation")
    recovery_anchor_ref = typed(70, "recovery_anchor")
    rollback_hint_ref = typed(71, "rollback_hint")

    return {
        "experiment_intent": ExperimentIntentState(
            identity=identity(500, L2StateKind.EXPERIMENT),
            status=status(),
            experiment_intent_ref=experiment_ref,
            candidate_ref=candidate_ref,
            experiment_kind=ExperimentKind.RETRIEVAL_QUALITY,
            target_ref=typed(53, "retrieval_quality"),
            hypothesis_summary="retrieval quality may improve after candidate change",
            expected_signal_summary="observation quality reference improves",
        ),
        "experiment_design": ExperimentDesignState(
            identity=identity(501, L2StateKind.EXPERIMENT),
            status=status(),
            design_ref=design_ref,
            experiment_intent_ref=experiment_ref,
            baseline_refs=(typed(54, "baseline"),),
            candidate_refs=(candidate_ref,),
            metric_refs=(typed(55, "metric"),),
            design_summary="design is only a state reference",
            experiment_status=ExperimentStatus.DESIGNED,
        ),
        "experiment_observation": ExperimentObservationState(
            identity=identity(502, L2StateKind.EXPERIMENT),
            status=status(),
            experiment_observation_ref=typed(56, "experiment_observation"),
            design_ref=design_ref,
            observation_frame_refs=(typed(57, "observation_frame"),),
            metric_refs=(typed(55, "metric"),),
            evidence_refs=(typed(58, "evidence"),),
            observation_summary="observation is only referenced",
        ),
        "experiment_result": ExperimentResultState(
            identity=identity(503, L2StateKind.EXPERIMENT),
            status=status(),
            result_ref=result_ref,
            design_ref=design_ref,
            observation_refs=(typed(56, "experiment_observation"),),
            result_summary="result is only referenced",
            confidence=0.5,
            validation_refs=(validation_ref,),
        ),
        "experiment_comparison": ExperimentComparisonState(
            identity=identity(504, L2StateKind.EXPERIMENT),
            status=status(),
            comparison_ref=typed(59, "experiment_comparison"),
            baseline_result_ref=typed(54, "baseline"),
            candidate_result_ref=result_ref,
            comparison_status=ExperimentComparisonStatus.DIFFERENCE_REFERENCED,
            difference_summary="difference reference only",
        ),
        "experiment_rollback_hint": ExperimentRollbackHintState(
            identity=identity(505, L2StateKind.RECOVERY),
            status=status(),
            rollback_hint_ref=typed(63, "experiment_rollback_hint"),
            experiment_ref=experiment_ref,
            recovery_point_refs=(recovery_anchor_ref,),
            reason_summary="experiment needs recovery anchor",
        ),
        "validation_intent": ValidationIntentState(
            identity=identity(600, L2StateKind.VALIDATION),
            status=status(),
            validation_intent_ref=validation_intent_ref,
            intent_kind=ValidationIntentKind.CANDIDATE,
            target_ref=candidate_ref,
            candidate_ref=candidate_ref,
            summary="candidate validation intent only",
        ),
        "validation_ref": ValidationRefState(
            identity=identity(601, L2StateKind.VALIDATION),
            status=status(),
            validation_ref=validation_ref,
            validation_intent_ref=validation_intent_ref,
            test_refs=(typed(62, "test"),),
            result_refs=(typed(64, "test_result"),),
            outcome_status=ValidationOutcomeRefStatus.REFERENCED,
            summary="validation result reference only",
        ),
        "verification_ref": VerificationRefState(
            identity=identity(602, L2StateKind.VALIDATION),
            status=status(),
            verification_ref=typed(65, "verification"),
            target_ref=candidate_ref,
            invariant_refs=(typed(66, "invariant"),),
            outcome_status=ValidationOutcomeRefStatus.PARTIAL,
        ),
        "test_plan": TestPlanRefState(
            identity=identity(603, L2StateKind.VALIDATION),
            status=status(),
            test_plan_ref=typed(67, "test_plan"),
            target_ref=candidate_ref,
            test_refs=(typed(62, "test"),),
            readiness_status=ValidationReadinessStatus.READY,
            plan_summary="test plan reference only",
        ),
        "candidate_validation": CandidateValidationState(
            identity=identity(604, L2StateKind.VALIDATION),
            status=status(),
            candidate_validation_ref=typed(68, "candidate_validation"),
            candidate_ref=candidate_ref,
            validation_intent_ref=validation_intent_ref,
            validation_refs=(validation_ref,),
            readiness_status=ValidationReadinessStatus.DECLARED,
        ),
        "recovery_validation": RecoveryValidationState(
            identity=identity(605, L2StateKind.VALIDATION),
            status=status(),
            recovery_validation_ref=typed(69, "recovery_validation"),
            recovery_point_ref=recovery_anchor_ref,
            rollback_hint_ref=rollback_hint_ref,
            validation_refs=(validation_ref,),
            readiness_status=ValidationReadinessStatus.EVIDENCE_MISSING,
        ),
        "recovery_anchor": RecoveryAnchorState(
            identity=identity(700, L2StateKind.RECOVERY),
            status=status(),
            recovery_anchor_ref=recovery_anchor_ref,
            anchor_kind=RecoveryAnchorKind.STATE_SNAPSHOT,
            target_ref=candidate_ref,
            snapshot_ref=typed(72, "state_snapshot"),
            summary="snapshot reference only",
        ),
        "rollback_hint": RollbackHintState(
            identity=identity(701, L2StateKind.RECOVERY),
            status=status(),
            rollback_hint_ref=rollback_hint_ref,
            target_ref=candidate_ref,
            recovery_anchor_refs=(recovery_anchor_ref,),
            reason_summary="rollback hint only",
        ),
        "recovery_readiness": RecoveryReadinessState(
            identity=identity(702, L2StateKind.RECOVERY),
            status=status(),
            recovery_readiness_ref=typed(73, "recovery_readiness"),
            target_ref=candidate_ref,
            recovery_anchor_refs=(recovery_anchor_ref,),
            validation_refs=(validation_ref,),
            readiness_status=RecoveryReadinessStatus.READY,
        ),
        "recovery_outcome_ref": RecoveryOutcomeRefState(
            identity=identity(703, L2StateKind.RECOVERY),
            status=status(),
            recovery_outcome_ref=typed(74, "recovery_outcome"),
            rollback_hint_ref=rollback_hint_ref,
            recovery_validation_refs=(typed(69, "recovery_validation"),),
            outcome_status=RecoveryOutcomeStatus.NOT_REFERENCED,
            outcome_summary="outcome not produced in this layer",
        ),
        "recovery_link": RecoveryLinkState(
            identity=identity(704, L2StateKind.RECOVERY),
            status=status(),
            recovery_link_ref=typed(75, "recovery_link"),
            source_state_ref=candidate_ref,
            recovery_anchor_refs=(recovery_anchor_ref,),
            rollback_hint_refs=(rollback_hint_ref,),
            recovery_validation_refs=(typed(69, "recovery_validation"),),
            continuity_refs=(typed(76, "continuity"),),
        ),
    }


def test_l2_phase7_experiment_validation_recovery_objects_are_frozen_dataclasses():
    for name, item in build_experiment_validation_recovery_objects().items():
        assert is_dataclass(item), name
        assert getattr(type(item), "__slots__", None) is not None, name
        with pytest.raises(FrozenInstanceError):
            item.schema_version = "changed"  # type: ignore[misc]


def test_l2_phase7_experiment_validation_recovery_refuse_invalid_scores():
    base = build_experiment_validation_recovery_objects()["experiment_result"]
    with pytest.raises(ValueError):
        ExperimentResultState(identity=base.identity, status=base.status, confidence=1.2)


def test_l2_phase7_experiment_validation_recovery_have_identity_status_schema():
    for name, item in build_experiment_validation_recovery_objects().items():
        field_names = {field.name for field in fields(item)}
        assert {"identity", "status", "schema_version"}.issubset(field_names), name
        assert item.schema_version == "0.1", name


def test_l2_phase7_status_enums_keep_state_only_semantics():
    assert ValidationReadinessStatus.READY.value == "ready"
    assert RecoveryReadinessStatus.READY.value == "ready"
    assert ExperimentStatus.RESULT_REFERENCED.value == "result_referenced"
