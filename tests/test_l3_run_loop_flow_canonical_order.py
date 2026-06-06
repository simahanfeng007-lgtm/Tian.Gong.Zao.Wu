from tiangong_kernel.l3_orchestration import CanonicalRunLoopFlowBundle, OrchestrationFlowKind


def test_l3_run_loop_flow_canonical_bundle_contains_main_chain_nodes():
    bundle = CanonicalRunLoopFlowBundle()
    expected = (
        OrchestrationFlowKind.CONTEXT_PREPARATION,
        OrchestrationFlowKind.MODEL_INTENT,
        OrchestrationFlowKind.SKILL_TOOL_RELEASE,
        OrchestrationFlowKind.ACTION_INTENT,
        OrchestrationFlowKind.EFFECT_REQUEST,
        OrchestrationFlowKind.DECISION,
        OrchestrationFlowKind.LEASE_VALIDATION,
        OrchestrationFlowKind.EXECUTION_HANDOFF,
        OrchestrationFlowKind.OBSERVATION_FEEDBACK,
        OrchestrationFlowKind.EVENT_APPEND,
        OrchestrationFlowKind.STATE_TRANSITION,
        OrchestrationFlowKind.AUDIT,
        OrchestrationFlowKind.RECOVERY,
        OrchestrationFlowKind.HUMAN_APPROVAL,
        OrchestrationFlowKind.SCHEDULE_TRIGGER_TIMER,
    )
    assert bundle.ordered_flow_kinds == expected
    assert bundle.no_execution is True
    assert bundle.no_decision is True
    assert bundle.no_persistence is True
