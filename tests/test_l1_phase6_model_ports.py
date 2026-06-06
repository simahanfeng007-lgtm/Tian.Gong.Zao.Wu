import inspect
from dataclasses import is_dataclass
from pathlib import Path
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolRef
from tiangong_kernel.l1_ports.model_envelope_ports import ModelRequestEnvelope, ModelResponseEnvelope
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.model_ports as ports


PORT_CLASSES = [
    ports.ModelPort,
    ports.ModelSessionPort,
    ports.ModelMessagePort,
    ports.ModelContextPort,
    ports.ModelAvailableActionViewPort,
]
DATA_CLASSES = [
    ports.ModelSessionBoundary,
    ports.ModelSkillView,
    ports.ModelToolGroupView,
    ports.ModelAvailableActionView,
    ports.ModelContextView,
    ports.ModelRequest,
    ports.ModelResponse,
    ports.ModelSessionRequest,
    ports.ModelSessionResponse,
    ports.ModelMessageRequest,
    ports.ModelMessageResponse,
    ports.ModelContextRequest,
    ports.ModelContextResponse,
    ports.ModelAvailableActionViewRequest,
    ports.ModelAvailableActionViewResponse,
]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase6_model_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase6_model_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase6_model_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase6_model_ports_reuse_l0_refs_and_l1_model_envelopes():
    assert get_type_hints(ports.ModelSessionBoundary)["session_ref"] is ResourceRef
    assert get_type_hints(ports.ModelSkillView)["skill_ref"] is SkillRef
    assert get_type_hints(ports.ModelToolGroupView)["visible_tool_refs"] == tuple[ToolRef, ...]
    assert get_type_hints(ports.ModelAvailableActionView)["skill_views"] == tuple[ports.ModelSkillView, ...]
    assert get_type_hints(ports.ModelContextView)["tool_group_views"] == tuple[ports.ModelToolGroupView, ...]
    assert get_type_hints(ports.ModelRequest)["request_envelope"] is ModelRequestEnvelope
    assert get_type_hints(ports.ModelResponse)["response_envelope"] == ModelResponseEnvelope | None


def test_phase6_model_ports_do_not_restore_old_or_real_model_objects():
    text = Path(ports.__file__).read_text(encoding="utf-8")
    forbidden = [
        "CapabilityPort",
        "AbilityPackagePort",
        "ModelRouter",
        "ModelExecutor",
        "PromptEngine",
        "api_key",
        "bearer token",
        "requests.post",
        "httpx.post",
        "model.call",
    ]
    assert [item for item in forbidden if item in text] == []
