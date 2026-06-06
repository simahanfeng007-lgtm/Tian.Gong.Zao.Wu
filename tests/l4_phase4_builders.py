from l3_phase1_builders import typed
from tiangong_kernel.l3_orchestration.intent_envelope import ActionIntentRef, ModelIntentRef, ToolIntentParameterSpecRef, ToolIntentRef
from tiangong_kernel.l4_action_grounding import (
    AdapterInputEnvelope,
    AdapterMode,
    DisabledRealModelToolAdapterStub,
    DryRunModelAdapter,
    DryRunToolAdapter,
    FakeModelAdapter,
    FakeToolAdapter,
    L3IntentBinding,
    ModelActionRequest,
    ToolActionRequest,
    ToolArgumentEnvelope,
    ToolCallEnvelope,
    ToolGroupActionContext,
)


def phase4_ref(offset: int, ref_type: str):
    return typed(7000 + offset, ref_type)


def adapter_input(action_kind="model_action", mode=AdapterMode.DRY_RUN):
    return AdapterInputEnvelope(
        envelope_ref=phase4_ref(1, "adapter_input"),
        action_kind=action_kind,
        envelope_type=f"{action_kind}_request",
        mode=mode,
    )


def model_intent_ref():
    return ModelIntentRef(intent_ref=phase4_ref(2, "model_intent"), step_ref=phase4_ref(3, "execution_step"))


def tool_intent_ref():
    return ToolIntentRef(
        intent_ref=phase4_ref(4, "tool_intent"),
        tool_group_ref=phase4_ref(5, "tool_group"),
        tool_ref=phase4_ref(6, "tool"),
        step_ref=phase4_ref(3, "execution_step"),
    )


def action_intent_ref():
    return ActionIntentRef(
        intent_ref=phase4_ref(7, "action_intent"),
        action_label="test_action",
        tool_intent_ref=phase4_ref(4, "tool_intent"),
        step_ref=phase4_ref(3, "execution_step"),
    )


def tool_arguments():
    return ToolArgumentEnvelope(
        argument_ref=phase4_ref(8, "tool_argument"),
        argument_items=(("query", "hello"),),
        parameter_spec_refs=(ToolIntentParameterSpecRef(phase4_ref(9, "tool_parameter_spec"), "query").parameter_spec_ref,),
    )


def tool_group_context():
    return ToolGroupActionContext(
        context_ref=phase4_ref(10, "tool_group_context"),
        tool_group_ref=phase4_ref(5, "tool_group"),
        skill_ref=phase4_ref(11, "skill"),
        intent_ref=phase4_ref(4, "tool_intent"),
        available_tool_refs=(phase4_ref(6, "tool"),),
        release_scope_ref=phase4_ref(12, "release_scope"),
        l3_release_advice_ref=phase4_ref(13, "tool_group_release_advice"),
    )


def tool_call():
    return ToolCallEnvelope(
        call_ref=phase4_ref(14, "tool_call"),
        tool_ref=phase4_ref(6, "tool"),
        tool_group_ref=phase4_ref(5, "tool_group"),
        action_intent_ref=phase4_ref(7, "action_intent"),
        tool_intent_ref=phase4_ref(4, "tool_intent"),
        arguments_envelope=tool_arguments(),
    )


def model_request(mode=AdapterMode.DRY_RUN):
    return ModelActionRequest(
        request_ref=phase4_ref(15, "model_action_request"),
        model_target_ref=phase4_ref(16, "model_target"),
        prompt_or_message_ref=phase4_ref(17, "prompt_or_message"),
        input_envelope=adapter_input("model_action", mode),
        l3_model_intent_ref=phase4_ref(2, "model_intent"),
        l3_action_intent_ref=phase4_ref(7, "action_intent"),
    )


def tool_request(mode=AdapterMode.DRY_RUN):
    return ToolActionRequest(
        request_ref=phase4_ref(18, "tool_action_request"),
        tool_ref=phase4_ref(6, "tool"),
        tool_group_ref=phase4_ref(5, "tool_group"),
        arguments_envelope=tool_arguments(),
        tool_call_envelope=tool_call(),
        tool_group_context=tool_group_context(),
        l3_tool_intent_ref=phase4_ref(4, "tool_intent"),
        l3_action_intent_ref=phase4_ref(7, "action_intent"),
    )


def l3_binding():
    return L3IntentBinding(
        binding_ref=phase4_ref(19, "l3_intent_binding"),
        model_intent_ref=model_intent_ref(),
        tool_intent_ref=tool_intent_ref(),
        action_intent_ref=action_intent_ref(),
        tool_group_release_ref=phase4_ref(13, "tool_group_release_advice"),
        execution_request_ref=phase4_ref(20, "execution_request"),
        execution_step_ref=phase4_ref(3, "execution_step"),
    )


def adapters():
    return FakeModelAdapter(), FakeToolAdapter(), DryRunModelAdapter(), DryRunToolAdapter(), DisabledRealModelToolAdapterStub()
