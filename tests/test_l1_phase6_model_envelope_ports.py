import inspect
from dataclasses import is_dataclass
from pathlib import Path
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.action import ActionIntent
from tiangong_kernel.l0_primitives.content import ContentRef, PayloadRef
from tiangong_kernel.l0_primitives.errors import CoreError
from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.model_envelope_ports as ports


PORT_CLASSES = [
    ports.ModelRequestEnvelopePort,
    ports.ModelResponseEnvelopePort,
    ports.ModelToolCallEnvelopePort,
    ports.ModelObservationEnvelopePort,
    ports.ModelErrorEnvelopePort,
]
DATA_CLASSES = [
    ports.ModelRequestEnvelope,
    ports.ModelResponseEnvelope,
    ports.ModelToolCallEnvelope,
    ports.ModelObservationEnvelope,
    ports.ModelErrorEnvelope,
    ports.ModelRequestEnvelopeRequest,
    ports.ModelRequestEnvelopeResponse,
    ports.ModelResponseEnvelopeRequest,
    ports.ModelResponseEnvelopeResponse,
    ports.ModelToolCallEnvelopeRequest,
    ports.ModelToolCallEnvelopeResponse,
    ports.ModelObservationEnvelopeRequest,
    ports.ModelObservationEnvelopeResponse,
    ports.ModelErrorEnvelopeRequest,
    ports.ModelErrorEnvelopeResponse,
]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase6_model_envelope_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase6_model_envelope_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase6_model_envelope_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase6_model_envelopes_reuse_l0_refs_and_express_intent_only():
    assert get_type_hints(ports.ModelRequestEnvelope)["request_id"] is RefId
    assert get_type_hints(ports.ModelRequestEnvelope)["trace_context"] is TraceContext
    assert get_type_hints(ports.ModelRequestEnvelope)["content_refs"] == tuple[ContentRef, ...]
    assert get_type_hints(ports.ModelRequestEnvelope)["payload_refs"] == tuple[PayloadRef, ...]
    assert get_type_hints(ports.ModelRequestEnvelope)["visible_skill_refs"] == tuple[SkillRef, ...]
    assert get_type_hints(ports.ModelRequestEnvelope)["visible_tool_group_refs"] == tuple[ResourceRef, ...]
    assert get_type_hints(ports.ModelResponseEnvelope)["action_intents"] == tuple[ActionIntent, ...]
    assert get_type_hints(ports.ModelToolCallEnvelope)["tool_ref"] == ToolRef | None
    assert get_type_hints(ports.ModelErrorEnvelope)["error"] == CoreError | None


def test_phase6_tool_call_envelope_port_does_not_execute_tools_or_call_models():
    text = Path(ports.__file__).read_text(encoding="utf-8")
    forbidden = [
        "ToolExecutor",
        "ModelExecutor",
        "ModelRouter",
        "CapabilityPort",
        "AbilityPackagePort",
        "openai",
        "deepseek",
        "qwen",
        "requests.post",
        "httpx.post",
        "tool.call",
        "model.call",
    ]
    assert [item for item in forbidden if item in text] == []
