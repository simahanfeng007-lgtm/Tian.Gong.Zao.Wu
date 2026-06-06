import inspect
from dataclasses import is_dataclass
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.action import ActionIntent
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.risk import RiskView
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolRef
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.control_boundary_ports as ports


PORT_CLASSES = [
    ports.BoundaryCheckPort,
    ports.BoundaryExplainPort,
    ports.BoundaryAlternativePort,
    ports.BoundaryViolationRecordPort,
    ports.ToolReleaseBoundaryPort,
]
DATA_CLASSES = [
    ports.ControlBoundary,
    ports.ToolReleaseBoundary,
    ports.BoundaryCheckRequest,
    ports.BoundaryCheckResponse,
    ports.BoundaryExplainRequest,
    ports.BoundaryExplainResponse,
    ports.BoundaryAlternativeRequest,
    ports.BoundaryAlternativeResponse,
    ports.BoundaryViolationRecordRequest,
    ports.BoundaryViolationRecordResponse,
    ports.ToolReleaseBoundaryRequest,
    ports.ToolReleaseBoundaryResponse,
]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase4_control_boundary_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase4_control_boundary_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase4_control_boundary_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase4_control_boundary_requests_use_l0_objects():
    check_hints = get_type_hints(ports.BoundaryCheckRequest)
    assert check_hints["action_intent"] is ActionIntent
    assert check_hints["risk_view"] == RiskView | None
    tool_hints = get_type_hints(ports.ToolReleaseBoundaryRequest)
    assert tool_hints["skill_ref"] is SkillRef
    assert get_origin(tool_hints["tool_refs"]) is tuple
    assert get_type_hints(ports.ToolReleaseBoundary)["skill_ref"] is SkillRef
    assert get_type_hints(ports.ToolReleaseBoundary)["tool_refs"] == tuple[ToolRef, ...]


def test_phase4_tool_release_boundary_does_not_define_real_release_method():
    methods = set(ports.ToolReleaseBoundaryPort.__abstractmethods__)
    assert methods == {"check_tool_release_boundary"}
