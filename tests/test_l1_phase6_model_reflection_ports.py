import inspect
from dataclasses import is_dataclass
from pathlib import Path
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolRef
from tiangong_kernel.l0_primitives.validation import TestRef
from tiangong_kernel.l1_ports.port_result import PortResult
from tiangong_kernel.l1_ports.skill_evolution_ports import SkillEvolutionHint, SkillIterationHint
import tiangong_kernel.l1_ports.model_reflection_ports as ports


PORT_CLASSES = [
    ports.ModelReflectionPort,
    ports.ModelSelfReviewPort,
    ports.ModelOutcomeAssessmentPort,
    ports.ModelEvolutionHintPort,
    ports.ModelIterationHintPort,
]
DATA_CLASSES = [
    ports.ModelReflection,
    ports.ModelSelfReview,
    ports.ModelOutcomeAssessment,
    ports.ModelEvolutionHint,
    ports.ModelIterationHint,
    ports.ModelReflectionRequest,
    ports.ModelReflectionResponse,
    ports.ModelSelfReviewRequest,
    ports.ModelSelfReviewResponse,
    ports.ModelOutcomeAssessmentRequest,
    ports.ModelOutcomeAssessmentResponse,
    ports.ModelEvolutionHintRequest,
    ports.ModelEvolutionHintResponse,
    ports.ModelIterationHintRequest,
    ports.ModelIterationHintResponse,
]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase6_model_reflection_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase6_model_reflection_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase6_model_reflection_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase6_model_reflection_reuses_l0_refs_and_phase5_evolution_hints():
    assert get_type_hints(ports.ModelReflection)["skill_ref"] == SkillRef | None
    assert get_type_hints(ports.ModelReflection)["tool_refs"] == tuple[ToolRef, ...]
    assert get_type_hints(ports.ModelSelfReview)["test_refs"] == tuple[TestRef, ...]
    assert get_type_hints(ports.ModelEvolutionHint)["skill_evolution_hint"] == SkillEvolutionHint | None
    assert get_type_hints(ports.ModelIterationHint)["skill_iteration_hint"] == SkillIterationHint | None


def test_phase6_model_reflection_only_defines_evidence_not_system_modification():
    text = Path(ports.__file__).read_text(encoding="utf-8")
    forbidden = [
        "SelfLearningPort",
        "EvolutionPort",
        "ModelExecutor",
        "ToolExecutor",
        "AbilityPackagePort",
        "CapabilityPort",
        "requests.post",
        "model.call",
        "tool.call",
    ]
    assert [item for item in forbidden if item in text] == []
