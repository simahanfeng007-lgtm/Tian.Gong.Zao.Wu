import inspect
from dataclasses import is_dataclass
from pathlib import Path
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.action import ActionIntent
from tiangong_kernel.l0_primitives.content import PayloadRef
from tiangong_kernel.l0_primitives.observation import ObservationRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolRef
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.tool_ports as ports


PORT_CLASSES = [
    ports.ToolReferencePort,
    ports.ToolDescriptionPort,
    ports.ToolInvocationIntentPort,
    ports.ToolInputBoundaryPort,
    ports.ToolOutputBoundaryPort,
    ports.ToolObservationPort,
]
DATA_CLASSES = [
    ports.ToolBoundary,
    ports.ToolDescriptionView,
    ports.ToolReferenceRequest,
    ports.ToolReferenceResponse,
    ports.ToolDescriptionRequest,
    ports.ToolDescriptionResponse,
    ports.ToolInvocationIntentRequest,
    ports.ToolInvocationIntentResponse,
    ports.ToolInputBoundaryRequest,
    ports.ToolInputBoundaryResponse,
    ports.ToolOutputBoundaryRequest,
    ports.ToolOutputBoundaryResponse,
    ports.ToolObservationRequest,
    ports.ToolObservationResponse,
]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase5_tool_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase5_tool_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase5_tool_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase5_tool_requests_use_l0_objects():
    assert get_type_hints(ports.ToolReferenceRequest)["tool_ref"] is ToolRef
    assert get_type_hints(ports.ToolDescriptionRequest)["skill_ref"] == SkillRef | None
    assert get_type_hints(ports.ToolInvocationIntentRequest)["action_intent"] is ActionIntent
    assert get_type_hints(ports.ToolInputBoundaryRequest)["payload_ref"] == PayloadRef | None
    assert get_type_hints(ports.ToolObservationRequest)["observation_ref"] is ObservationRef


def test_phase5_tool_ports_have_no_real_tool_call_terms():
    text = Path(ports.__file__).read_text(encoding="utf-8")
    forbidden = ["tool.call", "ToolExecutor", "subprocess", "socket", "requests", "open(", "read_text("]
    assert [item for item in forbidden if item in text] == []
