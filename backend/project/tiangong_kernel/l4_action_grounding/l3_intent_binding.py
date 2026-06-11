"""Structural binding from L3 intent refs to L4 action objects."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l3_orchestration.intent_envelope import ActionIntentRef, ModelIntentRef, ToolIntentRef

from .adapter_envelope import AdapterInputEnvelope
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true
from .model_action_request import ModelActionRequest
from .permit_ref import ActionPermitRef
from .tool_action_request import ToolActionRequest
from .tool_argument_envelope import ToolArgumentEnvelope
from .tool_call_envelope import ToolCallEnvelope
from .tool_group_action_context import ToolGroupActionContext


@dataclass(frozen=True, slots=True)
class L3IntentBinding:
    """Bind L3 intent references to L4 action objects; no orchestration or lookup."""

    binding_ref: TypedRef
    model_intent_ref: ModelIntentRef | None = None
    tool_intent_ref: ToolIntentRef | None = None
    action_intent_ref: ActionIntentRef | None = None
    tool_group_release_ref: TypedRef | None = None
    execution_request_ref: TypedRef | None = None
    execution_step_ref: TypedRef | None = None
    structural_only: bool = True
    mutates_l3: bool = False
    l4_generates_intent: bool = False
    resolves_skill_or_tool: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.structural_only, "L3IntentBinding.structural_only")
        ensure_false(self.mutates_l3, "L3IntentBinding.mutates_l3")
        ensure_false(self.l4_generates_intent, "L3IntentBinding.l4_generates_intent")
        ensure_false(self.resolves_skill_or_tool, "L3IntentBinding.resolves_skill_or_tool")
        ensure_schema_version(self.schema_version, "L3IntentBinding.schema_version")

    def to_model_action_request(
        self,
        *,
        request_ref: TypedRef,
        model_target_ref: TypedRef,
        prompt_or_message_ref: TypedRef,
        input_envelope: AdapterInputEnvelope,
        permit_ref: ActionPermitRef | None = None,
    ) -> ModelActionRequest:
        return ModelActionRequest(
            request_ref=request_ref,
            model_target_ref=model_target_ref,
            prompt_or_message_ref=prompt_or_message_ref,
            input_envelope=input_envelope,
            execution_context_ref=self.execution_request_ref,
            permit_ref=permit_ref,
            l3_model_intent_ref=None if self.model_intent_ref is None else self.model_intent_ref.intent_ref,
            l3_action_intent_ref=None if self.action_intent_ref is None else self.action_intent_ref.intent_ref,
            dry_run=True,
            production_path=False,
        )

    def to_tool_action_request(
        self,
        *,
        request_ref: TypedRef,
        tool_ref: TypedRef,
        tool_group_ref: TypedRef,
        arguments_envelope: ToolArgumentEnvelope,
        permit_ref: ActionPermitRef | None = None,
    ) -> ToolActionRequest:
        call_envelope = ToolCallEnvelope(
            call_ref=request_ref,
            tool_ref=tool_ref,
            tool_group_ref=tool_group_ref,
            action_intent_ref=None if self.action_intent_ref is None else self.action_intent_ref.intent_ref,
            tool_intent_ref=None if self.tool_intent_ref is None else self.tool_intent_ref.intent_ref,
            arguments_envelope=arguments_envelope,
            permit_ref=permit_ref,
            dry_run=True,
            production_path=False,
        )
        context = ToolGroupActionContext(
            context_ref=tool_group_ref,
            tool_group_ref=tool_group_ref,
            skill_ref=None if self.tool_intent_ref is None else self.tool_intent_ref.tool_group_ref,
            intent_ref=None if self.tool_intent_ref is None else self.tool_intent_ref.intent_ref,
            available_tool_refs=(tool_ref,),
            l3_release_advice_ref=self.tool_group_release_ref,
        )
        return ToolActionRequest(
            request_ref=request_ref,
            tool_ref=tool_ref,
            tool_group_ref=tool_group_ref,
            arguments_envelope=arguments_envelope,
            tool_call_envelope=call_envelope,
            tool_group_context=context,
            permit_ref=permit_ref,
            execution_context_ref=self.execution_request_ref,
            l3_tool_intent_ref=None if self.tool_intent_ref is None else self.tool_intent_ref.intent_ref,
            l3_action_intent_ref=None if self.action_intent_ref is None else self.action_intent_ref.intent_ref,
            dry_run=True,
            production_path=False,
        )
