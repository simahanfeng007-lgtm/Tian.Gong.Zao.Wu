import inspect
from dataclasses import is_dataclass
from pathlib import Path
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolRef
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.skill_ports as ports


PORT_CLASSES = [
    ports.SkillReferencePort,
    ports.SkillRegistryPort,
    ports.SkillQueryPort,
    ports.SkillExposurePort,
    ports.SkillFlowPort,
    ports.SkillBoundaryPort,
]
DATA_CLASSES = [
    ports.SkillBoundary,
    ports.SkillExposureView,
    ports.SkillFlowView,
    ports.SkillReferenceRequest,
    ports.SkillReferenceResponse,
    ports.SkillRegistryRequest,
    ports.SkillRegistryResponse,
    ports.SkillQueryRequest,
    ports.SkillQueryResponse,
    ports.SkillExposureRequest,
    ports.SkillExposureResponse,
    ports.SkillFlowRequest,
    ports.SkillFlowResponse,
    ports.SkillBoundaryRequest,
    ports.SkillBoundaryResponse,
]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase5_skill_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase5_skill_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase5_skill_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase5_skill_requests_use_l0_skill_and_tool_objects():
    assert get_type_hints(ports.SkillReferenceRequest)["skill_ref"] is SkillRef
    assert get_type_hints(ports.SkillExposureView)["skill_ref"] is SkillRef
    assert get_type_hints(ports.SkillExposureView)["tool_group_ref"] == ResourceRef | None
    assert get_type_hints(ports.SkillFlowView)["required_tool_refs"] == tuple[ToolRef, ...]


def test_phase5_skill_exposure_does_not_expose_internal_ports_or_old_objects():
    text = Path(ports.__file__).read_text(encoding="utf-8")
    forbidden = ["CapabilityPort", "AbilityPackagePort", "PluginHost", "ToolExecutor", "ModelExecutor", "神枢"]
    assert [item for item in forbidden if item in text] == []
