import inspect
from dataclasses import is_dataclass
from pathlib import Path
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.action import ActionIntent
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolRef
from tiangong_kernel.l1_ports.control_boundary_ports import ToolReleaseBoundary
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.tool_release_ports as ports


PORT_CLASSES = [
    ports.ToolReleaseIntentPort,
    ports.ToolReleaseRequestPort,
    ports.ToolReleaseResultPort,
    ports.ToolReleaseViewPort,
    ports.ToolReleaseRevocationPort,
]
DATA_CLASSES = [
    ports.ToolReleaseView,
    ports.ToolReleaseIntentRequest,
    ports.ToolReleaseIntentResponse,
    ports.ToolReleaseRequest,
    ports.ToolReleaseResponse,
    ports.ToolReleaseResultRequest,
    ports.ToolReleaseResultResponse,
    ports.ToolReleaseViewRequest,
    ports.ToolReleaseViewResponse,
    ports.ToolReleaseRevocationRequest,
    ports.ToolReleaseRevocationResponse,
]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase5_tool_release_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase5_tool_release_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase5_tool_release_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase5_tool_release_reuses_l0_refs_and_phase4_boundary():
    assert get_type_hints(ports.ToolReleaseIntentRequest)["skill_ref"] is SkillRef
    assert get_type_hints(ports.ToolReleaseIntentRequest)["tool_group_ref"] is ResourceRef
    assert get_type_hints(ports.ToolReleaseIntentRequest)["action_intent"] == ActionIntent | None
    assert get_type_hints(ports.ToolReleaseView)["visible_tool_refs"] == tuple[ToolRef, ...]
    assert get_type_hints(ports.ToolReleaseView)["boundary"] == ToolReleaseBoundary | None


def test_phase5_tool_release_only_defines_protocol_not_real_release():
    text = Path(ports.__file__).read_text(encoding="utf-8")
    forbidden = ["release_tools", "ToolExecutor", "AbilityPackage", "AbilityRouter", "grant_lease", "open("]
    assert [item for item in forbidden if item in text] == []
