import inspect
from dataclasses import is_dataclass
from pathlib import Path
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolRef
from tiangong_kernel.l1_ports.port_boundary import PortBoundary
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.tool_gap_ports as ports


PORT_CLASSES = [
    ports.SkillGapReportPort,
    ports.ToolNeedReportPort,
    ports.ToolGroupGapReportPort,
    ports.ToolGapBoundaryPort,
]
DATA_CLASSES = [
    ports.SkillGapReport,
    ports.ToolNeedReport,
    ports.ToolGroupGapReport,
    ports.ToolGapBoundary,
    ports.SkillGapReportRequest,
    ports.SkillGapReportResponse,
    ports.ToolNeedReportRequest,
    ports.ToolNeedReportResponse,
    ports.ToolGroupGapReportRequest,
    ports.ToolGroupGapReportResponse,
    ports.ToolGapBoundaryRequest,
    ports.ToolGapBoundaryResponse,
]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase5_tool_gap_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase5_tool_gap_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase5_tool_gap_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase5_tool_gap_reuses_l0_refs_and_l1_boundary():
    assert get_type_hints(ports.SkillGapReport)["skill_ref"] == SkillRef | None
    assert get_type_hints(ports.ToolNeedReport)["tool_ref"] == ToolRef | None
    assert get_type_hints(ports.ToolGroupGapReport)["tool_group_ref"] == ResourceRef | None
    assert get_type_hints(ports.ToolGroupGapReport)["missing_tool_refs"] == tuple[ToolRef, ...]
    assert get_type_hints(ports.ToolGapBoundary)["boundary"] == PortBoundary | None


def test_phase5_tool_gap_only_reports_not_real_tool_production():
    text = Path(ports.__file__).read_text(encoding="utf-8")
    forbidden = ["CapabilityPort", "AbilityPackagePort", "PluginHost", "ToolExecutor", "ModelExecutor", "神枢", "release_tools", "open("]
    assert [item for item in forbidden if item in text] == []
