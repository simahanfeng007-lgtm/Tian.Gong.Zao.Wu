from dataclasses import replace

from l3_phase1_builders import build_l3_objects, typed
from tiangong_kernel.l3_orchestration import (
    ContinuityEvaluationSet,
    LifecycleTransitionCandidate,
    LifecycleTransitionIntent,
    OrchestrationLifecycleKind,
    ProcessStateTransitionAdvice,
    ResumeAdviceKind,
    RunContinuityEvaluation,
    RunOrchestrationPlan,
    RunOrchestrationRef,
    RunProgressSnapshot,
    RunResumeAdvice,
    StepProgressSnapshot,
    StepReadinessEvaluation,
    StepResumeAdvice,
    StepSequence,
    StepTransitionAdvice,
    StepTransitionCandidate,
    StepTransitionKind,
    TaskContinuityEvaluation,
    TaskInterruptionAdvice,
    TaskOrchestrationPlan,
    TaskOrchestrationRef,
    TaskProgressSnapshot,
    TaskResumeAdvice,
    TurnCarryoverHint,
    TurnCarryoverKind,
    TurnContinuityEvaluation,
    TurnOrchestrationPlan,
    TurnOrchestrationRef,
    TurnSequenceRef,
    build_cancellation_suitability_score,
    build_context_carryover_score,
    build_continuity_index,
    build_interruption_severity_score,
    build_math_score_vector_from_continuity,
    build_process_state_transition_advice,
    build_progress_coherence_score,
    build_recovery_priority_score,
    build_resumability_index,
    build_run_state_view_from_context,
    build_step_readiness_score,
)


def build_l3_phase2_objects():
    phase1 = build_l3_objects()
    context = phase1["context"]
    affective_input = phase1["affective_input"]
    dynamic_input = phase1["dynamic_input"]

    run_ref = typed(800, "run_orchestration")
    task_ref = typed(801, "task_orchestration")
    turn_1 = typed(802, "turn_orchestration")
    turn_2 = typed(803, "turn_orchestration")
    step_1 = typed(804, "step_orchestration")
    step_2 = typed(805, "step_orchestration")
    candidate_ref = typed(806, "step_transition_candidate")

    run_ref_obj = RunOrchestrationRef(
        run_ref=run_ref,
        source_request_ref=phase1["request"].identity.orchestration_ref,
        source_context_ref=context.identity.orchestration_ref,
    )
    run_view = build_run_state_view_from_context(context, run_ref_obj, OrchestrationLifecycleKind.PAUSED)

    step_sequence = StepSequence(
        sequence_ref=typed(807, "step_sequence"),
        run_ref=run_ref,
        task_ref=task_ref,
        step_refs=(step_1, step_2),
        completed_step_refs=(step_1,),
        active_step_ref=step_1,
        next_step_ref=step_2,
        lifecycle=OrchestrationLifecycleKind.PAUSED,
        sequence_notes=("phase2 sequence fixture",),
    )
    step_candidate = StepTransitionCandidate(
        candidate_ref=candidate_ref,
        sequence_ref=step_sequence.sequence_ref,
        source_step_ref=step_1,
        target_step_ref=step_2,
        transition_kind=StepTransitionKind.ADVANCE_NEXT,
        intent=LifecycleTransitionIntent.ADVANCE_TO_NEXT_STEP,
        current_lifecycle=OrchestrationLifecycleKind.PAUSED,
        candidate_lifecycle=OrchestrationLifecycleKind.RESUMABLE,
        required_state_refs=(typed(808, "required_state"),),
        score_hint=0.8,
        reason_items=("next step exists",),
    )
    step_snapshot = StepProgressSnapshot(
        snapshot_ref=typed(809, "step_progress_snapshot"),
        step_ref=step_1,
        task_ref=task_ref,
        lifecycle=OrchestrationLifecycleKind.PAUSED,
        progress_ratio=0.5,
        required_state_refs=step_candidate.required_state_refs,
        available_state_refs=step_candidate.required_state_refs,
        summary="step snapshot fixture",
    )
    task_snapshot = TaskProgressSnapshot(
        snapshot_ref=typed(810, "task_progress_snapshot"),
        task_ref=task_ref,
        run_ref=run_ref,
        lifecycle=OrchestrationLifecycleKind.PAUSED,
        step_refs=step_sequence.step_refs,
        completed_step_refs=step_sequence.completed_step_refs,
        active_step_ref=step_1,
        progress_ratio=0.5,
        summary="task snapshot fixture",
    )
    run_snapshot = RunProgressSnapshot(
        snapshot_ref=typed(811, "run_progress_snapshot"),
        run_ref=run_ref,
        lifecycle=OrchestrationLifecycleKind.PAUSED,
        task_refs=(task_ref,),
        active_task_ref=task_ref,
        progress_ratio=0.5,
        summary="run snapshot fixture",
    )
    carryover_hint = TurnCarryoverHint(
        hint_ref=typed(812, "turn_carryover_hint"),
        carryover_kind=TurnCarryoverKind.PARTIAL_RESULT,
        source_turn_ref=turn_1,
        target_turn_ref=turn_2,
        related_state_refs=(step_1,),
        carryover_value=0.9,
        confidence=0.8,
        summary="carryover fixture",
    )

    continuity_index = build_continuity_index(step_sequence, (carryover_hint,))
    resumability_index = build_resumability_index(
        OrchestrationLifecycleKind.PAUSED,
        next_step_refs=(step_2,),
    )
    severity = build_interruption_severity_score(OrchestrationLifecycleKind.PAUSED)
    readiness = build_step_readiness_score(step_candidate, step_candidate.required_state_refs)
    progress = build_progress_coherence_score(step_sequence, task_snapshot, run_snapshot)
    carryover_score = build_context_carryover_score((carryover_hint,))
    recovery = build_recovery_priority_score(severity, resumability_index, dynamic_input, affective_input)
    cancellation = build_cancellation_suitability_score(severity, resumability_index, progress)
    continuity_set = ContinuityEvaluationSet(
        evaluation_ref=typed(813, "continuity_evaluation"),
        subject_ref=run_ref,
        continuity_index=continuity_index,
        resumability_index=resumability_index,
        interruption_severity=severity,
        step_readiness=readiness,
        progress_coherence=progress,
        context_carryover=carryover_score,
        recovery_priority=recovery,
        cancellation_suitability=cancellation,
        affective_input=affective_input,
        dynamic_drive_input=dynamic_input,
        summary="continuity set fixture",
    )
    math_score_vector = build_math_score_vector_from_continuity(continuity_set, typed(814, "math_score_vector"))
    continuity_set = replace(continuity_set, math_score_vector=math_score_vector)

    lifecycle_candidate = LifecycleTransitionCandidate(
        candidate_ref=typed(815, "lifecycle_transition_candidate"),
        subject_ref=run_ref,
        current_lifecycle=OrchestrationLifecycleKind.PAUSED,
        candidate_lifecycle=OrchestrationLifecycleKind.RESUMABLE,
        intent=LifecycleTransitionIntent.SUGGEST_RESUME_PATH,
        score_hint=recovery.value,
        reason_items=("resume path preferred",),
    )
    process_advice = build_process_state_transition_advice(lifecycle_candidate, typed(816, "l2_state_update_suggestion"))
    step_advice = StepTransitionAdvice(
        advice_ref=typed(817, "step_transition_advice"),
        candidate=step_candidate,
        suggested_lifecycle=OrchestrationLifecycleKind.RESUMABLE,
        transition_score=readiness.value,
        reason_summary="step advice fixture",
    )
    step_readiness_evaluation = StepReadinessEvaluation(
        evaluation_ref=typed(818, "step_readiness_evaluation"),
        candidate_ref=step_candidate.candidate_ref,
        progress_snapshot=step_snapshot,
        readiness_score_ref=typed(819, "step_readiness_score"),
        readiness_score_value=readiness.value,
        required_state_refs=step_candidate.required_state_refs,
        reason_summary="step readiness fixture",
    )
    step_resume = StepResumeAdvice(
        advice_ref=typed(820, "step_resume_advice"),
        step_ref=step_1,
        next_step_ref=step_2,
        advice_kind=ResumeAdviceKind.RESUME_NEXT_STEP,
        lifecycle=OrchestrationLifecycleKind.RESUMABLE,
        intent=LifecycleTransitionIntent.SUGGEST_RESUME_PATH,
        readiness_score=readiness,
        reason_summary="step resume fixture",
    )
    task_resume = TaskResumeAdvice(
        advice_ref=typed(821, "task_resume_advice"),
        task_ref=task_ref,
        active_step_ref=step_1,
        advice_kind=ResumeAdviceKind.RESUME_NEXT_STEP,
        resumability_index=resumability_index,
        step_resume_advices=(step_resume,),
        recovery_priority=recovery,
        reason_summary="task resume fixture",
    )
    task_interrupt = TaskInterruptionAdvice(
        advice_ref=typed(822, "task_interruption_advice"),
        task_ref=task_ref,
        current_lifecycle=OrchestrationLifecycleKind.PAUSED,
        suggested_lifecycle=OrchestrationLifecycleKind.RESUMABLE,
        suggested_intent=LifecycleTransitionIntent.SUGGEST_RESUME_PATH,
        reason_summary="task interruption fixture",
    )
    run_resume = RunResumeAdvice(
        advice_ref=typed(823, "run_resume_advice"),
        run_ref=run_ref,
        active_task_ref=task_ref,
        advice_kind=ResumeAdviceKind.RESUME_CURRENT,
        resumability_index=resumability_index,
        task_resume_advices=(task_resume,),
        recovery_priority=recovery,
        reason_summary="run resume fixture",
    )

    turn_ref = TurnOrchestrationRef(turn_ref=turn_2, run_ref=run_ref, task_ref=task_ref, turn_index=2)
    turn_sequence = TurnSequenceRef(
        sequence_ref=typed(824, "turn_sequence"),
        run_ref=run_ref,
        turn_refs=(turn_1, turn_2),
        current_turn_ref=turn_2,
        previous_turn_ref=turn_1,
    )
    turn_evaluation = TurnContinuityEvaluation(
        evaluation_ref=typed(825, "turn_continuity_evaluation"),
        sequence_ref=turn_sequence.sequence_ref,
        carryover_hint_refs=(carryover_hint.hint_ref,),
        context_carryover_score_ref=typed(826, "context_carryover_score"),
        context_carryover_score_value=carryover_score.value,
        confidence=0.8,
        reason_summary="turn continuity fixture",
    )
    turn_plan = TurnOrchestrationPlan(
        plan_ref=typed(827, "turn_orchestration_plan"),
        turn_ref=turn_ref,
        lifecycle=OrchestrationLifecycleKind.RESUMABLE,
        sequence_ref=turn_sequence,
        carryover_hints=(carryover_hint,),
        continuity_evaluation_ref=turn_evaluation.evaluation_ref,
        summary="turn plan fixture",
    )

    task_ref_obj = TaskOrchestrationRef(task_ref=task_ref, run_ref=run_ref, task_index=1)
    task_eval = TaskContinuityEvaluation(
        evaluation_ref=typed(828, "task_continuity_evaluation"),
        task_ref=task_ref,
        progress_snapshot=task_snapshot,
        step_sequence=step_sequence,
        continuity_evaluation=continuity_set,
        transition_advice_refs=(process_advice.advice_ref,),
        reason_summary="task continuity fixture",
    )
    task_plan = TaskOrchestrationPlan(
        plan_ref=typed(829, "task_orchestration_plan"),
        task_ref=task_ref_obj,
        lifecycle=OrchestrationLifecycleKind.RESUMABLE,
        progress_snapshot=task_snapshot,
        step_sequence=step_sequence,
        transition_candidates=(lifecycle_candidate,),
        transition_advices=(process_advice,),
        resume_advice=task_resume,
        interruption_advice=task_interrupt,
        continuity_evaluation_ref=task_eval.evaluation_ref,
        summary="task plan fixture",
    )
    run_eval = RunContinuityEvaluation(
        evaluation_ref=typed(830, "run_continuity_evaluation"),
        run_ref=run_ref,
        state_view=run_view,
        progress_snapshot=run_snapshot,
        continuity_evaluation=continuity_set,
        transition_advice_refs=(process_advice.advice_ref,),
        reason_summary="run continuity fixture",
    )
    run_plan = RunOrchestrationPlan(
        plan_ref=typed(831, "run_orchestration_plan"),
        run_ref=run_ref_obj,
        state_view=run_view,
        lifecycle=OrchestrationLifecycleKind.RESUMABLE,
        progress_snapshot=run_snapshot,
        transition_candidates=(lifecycle_candidate,),
        transition_advices=(process_advice,),
        resume_advice=run_resume,
        continuity_evaluation_ref=run_eval.evaluation_ref,
        summary="run plan fixture",
    )

    return {
        "run_ref": run_ref_obj,
        "run_view": run_view,
        "step_sequence": step_sequence,
        "step_candidate": step_candidate,
        "step_snapshot": step_snapshot,
        "task_snapshot": task_snapshot,
        "run_snapshot": run_snapshot,
        "carryover_hint": carryover_hint,
        "continuity_index": continuity_index,
        "resumability_index": resumability_index,
        "severity": severity,
        "readiness": readiness,
        "progress": progress,
        "carryover_score": carryover_score,
        "recovery": recovery,
        "cancellation": cancellation,
        "continuity_set": continuity_set,
        "math_score_vector": math_score_vector,
        "lifecycle_candidate": lifecycle_candidate,
        "process_advice": process_advice,
        "step_advice": step_advice,
        "step_readiness_evaluation": step_readiness_evaluation,
        "step_resume": step_resume,
        "task_resume": task_resume,
        "task_interrupt": task_interrupt,
        "run_resume": run_resume,
        "turn_ref": turn_ref,
        "turn_sequence": turn_sequence,
        "turn_evaluation": turn_evaluation,
        "turn_plan": turn_plan,
        "task_ref": task_ref_obj,
        "task_eval": task_eval,
        "task_plan": task_plan,
        "run_eval": run_eval,
        "run_plan": run_plan,
    }
