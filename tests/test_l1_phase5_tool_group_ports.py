import inspect
from dataclasses import is_dataclass
from pathlib import Path
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolRef
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.tool_group_ports as ports


PORT_CLASSES = [
    ports.ToolGroupReferencePort,
    ports.ToolGroupDescriptionPort,
    ports.ToolGroupQueryPort,
    ports.ToolGroupBoundaryPort,
    ports.ToolGroupLifecyclePort,
]
DATA_CLASSES = [
    ports.ToolGroupBoundary,
    ports.ToolGroupView,
    ports.ToolGroupReferenceRequest,
    ports.ToolGroupReferenceResponse,
    ports.ToolGroupDescriptionRequest,
    ports.ToolGroupDescriptionResponse,
    ports.ToolGroupQueryRequest,
    ports.ToolGroupQueryResponse,
    ports.ToolGroupBoundaryRequest,
    ports.ToolGroupBoundaryResponse,
    ports.ToolGroupLifecycleRequest,
    ports.ToolGroupLifecycleResponse,
]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase5_tool_group_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase5_tool_group_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase5_tool_group_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase5_tool_group_uses_resource_ref_instead_of_new_id():
    assert get_type_hints(ports.ToolGroupReferenceRequest)["tool_group_ref"] is ResourceRef
    assert get_type_hints(ports.ToolGroupView)["tool_group_ref"] is ResourceRef
    assert get_type_hints(ports.ToolGroupView)["skill_ref"] == SkillRef | None
    assert get_type_hints(ports.ToolGroupView)["tool_refs"] == tuple[ToolRef, ...]


def test_phase5_tool_group_not_old_package_or_real_release():
    text = Path(ports.__file__).read_text(encoding="utf-8")
    forbidden = ["AbilityPackage", "CapabilityPort", "AbilityRouter", "ToolExecutor", "release_tools", "open("]
    assert [item for item in forbidden if item in text] == []
