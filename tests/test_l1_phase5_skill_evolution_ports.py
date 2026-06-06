import inspect
from dataclasses import is_dataclass
from pathlib import Path
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolRef
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.skill_evolution_ports as ports


PORT_CLASSES = [
    ports.SkillEvolutionHintPort,
    ports.SkillIterationHintPort,
    ports.SkillVersionHintPort,
    ports.SkillCorrectionHintPort,
]
DATA_CLASSES = [
    ports.SkillEvolutionHint,
    ports.SkillIterationHint,
    ports.SkillVersionHint,
    ports.SkillCorrectionHint,
    ports.SkillEvolutionHintRequest,
    ports.SkillEvolutionHintResponse,
    ports.SkillIterationHintRequest,
    ports.SkillIterationHintResponse,
    ports.SkillVersionHintRequest,
    ports.SkillVersionHintResponse,
    ports.SkillCorrectionHintRequest,
    ports.SkillCorrectionHintResponse,
]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase5_skill_evolution_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase5_skill_evolution_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase5_skill_evolution_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase5_skill_evolution_reuses_l0_refs_and_phase5_relations():
    assert get_type_hints(ports.SkillEvolutionHint)["skill_ref"] is SkillRef
    assert get_type_hints(ports.SkillIterationHint)["affected_tool_refs"] == tuple[ToolRef, ...]
    assert get_type_hints(ports.SkillIterationHint)["affected_tool_group_ref"] == ResourceRef | None
    assert get_type_hints(ports.SkillVersionHint)["skill_ref"] is SkillRef


def test_phase5_skill_evolution_only_defines_hints_not_real_changes():
    text = Path(ports.__file__).read_text(encoding="utf-8")
    forbidden = ["CapabilityPort", "AbilityPackagePort", "PluginHost", "ToolExecutor", "ModelExecutor", "神枢", "model.call", "tool.call"]
    assert [item for item in forbidden if item in text] == []
