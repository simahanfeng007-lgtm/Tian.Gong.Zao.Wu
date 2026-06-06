from dataclasses import FrozenInstanceError, is_dataclass

import pytest

from tiangong_kernel.l3_orchestration import (
    ActionIntentFlow,
    AuditFlow,
    CanonicalRunLoopFlowBundle,
    ContextPreparationFlow,
    DecisionFlow,
    EffectRequestFlow,
    EventAppendFlow,
    ExecutionHandoffFlow,
    HumanApprovalFlow,
    LeaseValidationFlow,
    MainRunLoopFlowSpec,
    ModelIntentFlow,
    ObservationFeedbackFlow,
    OrchestrationFlowEdge,
    OrchestrationFlowInvariant,
    OrchestrationFlowKind,
    OrchestrationFlowNodeRef,
    OrchestrationFlowSpec,
    RecoveryFlow,
    RunOrchestrationFlow,
    ScheduleTriggerTimerFlow,
    SkillToolReleaseFlow,
    StateTransitionFlow,
    StepOrchestrationFlow,
)


FLOW_CLASSES = (
    OrchestrationFlowNodeRef,
    OrchestrationFlowEdge,
    OrchestrationFlowInvariant,
    OrchestrationFlowSpec,
    RunOrchestrationFlow,
    StepOrchestrationFlow,
    ContextPreparationFlow,
    ModelIntentFlow,
    SkillToolReleaseFlow,
    ActionIntentFlow,
    EffectRequestFlow,
    DecisionFlow,
    LeaseValidationFlow,
    ExecutionHandoffFlow,
    ObservationFeedbackFlow,
    EventAppendFlow,
    StateTransitionFlow,
    RecoveryFlow,
    AuditFlow,
    ScheduleTriggerTimerFlow,
    HumanApprovalFlow,
    CanonicalRunLoopFlowBundle,
)


FLOW_KIND_BY_CLASS = {
    ContextPreparationFlow: OrchestrationFlowKind.CONTEXT_PREPARATION,
    ModelIntentFlow: OrchestrationFlowKind.MODEL_INTENT,
    SkillToolReleaseFlow: OrchestrationFlowKind.SKILL_TOOL_RELEASE,
    ActionIntentFlow: OrchestrationFlowKind.ACTION_INTENT,
    EffectRequestFlow: OrchestrationFlowKind.EFFECT_REQUEST,
    DecisionFlow: OrchestrationFlowKind.DECISION,
    LeaseValidationFlow: OrchestrationFlowKind.LEASE_VALIDATION,
    ExecutionHandoffFlow: OrchestrationFlowKind.EXECUTION_HANDOFF,
    ObservationFeedbackFlow: OrchestrationFlowKind.OBSERVATION_FEEDBACK,
    EventAppendFlow: OrchestrationFlowKind.EVENT_APPEND,
    StateTransitionFlow: OrchestrationFlowKind.STATE_TRANSITION,
    RecoveryFlow: OrchestrationFlowKind.RECOVERY,
    AuditFlow: OrchestrationFlowKind.AUDIT,
    ScheduleTriggerTimerFlow: OrchestrationFlowKind.SCHEDULE_TRIGGER_TIMER,
    HumanApprovalFlow: OrchestrationFlowKind.HUMAN_APPROVAL,
}


def test_l3_run_loop_flow_classes_are_importable_frozen_slots():
    assert MainRunLoopFlowSpec is CanonicalRunLoopFlowBundle
    assert OrchestrationFlowKind.CONTEXT_PREPARATION.value == "context_preparation"
    for cls in FLOW_CLASSES:
        item = cls()
        assert is_dataclass(item)
        assert hasattr(type(item), "__slots__")
        with pytest.raises(FrozenInstanceError):
            item.schema_version = "changed"


def test_l3_run_loop_each_canonical_flow_kind_has_specialized_spec():
    covered = {flow_kind for flow_kind in FLOW_KIND_BY_CLASS.values()}
    for flow_kind in CanonicalRunLoopFlowBundle().ordered_flow_kinds:
        assert flow_kind in covered
    for cls, flow_kind in FLOW_KIND_BY_CLASS.items():
        assert cls().flow_kind is flow_kind
