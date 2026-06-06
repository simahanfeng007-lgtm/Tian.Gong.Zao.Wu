import inspect
from dataclasses import is_dataclass
from pathlib import Path
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.relation import DependencyRef, RelationRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolRef
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.tool_binding_ports as ports


PORT_CLASSES = [
    ports.SkillToolBindingPort,
    ports.ToolGroupBindingPort,
    ports.ToolDependencyPort,
    ports.ToolUsageFlowPort,
]
DATA_CLASSES = [
    ports.SkillToolBindingView,
    ports.ToolGroupBindingView,
    ports.ToolUsageFlowView,
    ports.SkillToolBindingRequest,
    ports.SkillToolBindingResponse,
    ports.ToolGroupBindingRequest,
    ports.ToolGroupBindingResponse,
    ports.ToolDependencyRequest,
    ports.ToolDependencyResponse,
    ports.ToolUsageFlowRequest,
    ports.ToolUsageFlowResponse,
]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase5_tool_binding_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase5_tool_binding_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase5_tool_binding_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase5_tool_binding_reuses_l0_relation_and_dependency_refs():
    assert get_type_hints(ports.SkillToolBindingRequest)["skill_ref"] is SkillRef
    assert get_type_hints(ports.SkillToolBindingRequest)["tool_refs"] == tuple[ToolRef, ...]
    assert get_type_hints(ports.ToolGroupBindingRequest)["tool_group_ref"] is ResourceRef
    assert get_type_hints(ports.ToolGroupBindingRequest)["relation_ref"] == RelationRef | None
    assert get_type_hints(ports.ToolDependencyRequest)["dependency_ref"] is DependencyRef


def test_phase5_tool_binding_has_no_real_binding_storage():
    text = Path(ports.__file__).read_text(encoding="utf-8")
    forbidden = ["write_text", "sqlite3", "scan", "ToolExecutor", "AbilityRouter", "open("]
    assert [item for item in forbidden if item in text] == []
