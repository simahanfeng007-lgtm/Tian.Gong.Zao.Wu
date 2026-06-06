import inspect
from dataclasses import is_dataclass
from pathlib import Path
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.learning import LearningRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l1_ports.model_feedback_ports import ModelLearningIntent
from tiangong_kernel.l1_ports.port_result import PortResult
from tiangong_kernel.l1_ports.tool_gap_ports import SkillGapReport, ToolNeedReport
import tiangong_kernel.l1_ports.learning_ports as ports

PORT_CLASSES = [ports.LearningIntentPort, ports.LearningTaskPort, ports.LearningEvidencePort, ports.LearningResultPort, ports.LearningBoundaryPort, ports.LearningFeedbackPort]
DATA_CLASSES = [ports.LearningIntent, ports.LearningCandidate, ports.LearningEvidence, ports.LearningResult, ports.LearningBoundary, ports.LearningFeedback, ports.LearningIntentRequest, ports.LearningIntentResponse, ports.LearningTaskRequest, ports.LearningTaskResponse, ports.LearningEvidenceRequest, ports.LearningEvidenceResponse, ports.LearningResultRequest, ports.LearningResultResponse, ports.LearningBoundaryRequest, ports.LearningBoundaryResponse, ports.LearningFeedbackRequest, ports.LearningFeedbackResponse]

def _return_is_result(method):
    return get_origin(get_type_hints(method)["return"]) in {CoreResult, PortResult}

def test_phase7_learning_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")

def test_phase7_learning_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))

def test_phase7_learning_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")

def test_phase7_learning_reuses_l0_learning_and_phase5_phase6_feedback_objects():
    assert get_type_hints(ports.LearningIntent)["learning_ref"] is LearningRef
    assert get_type_hints(ports.LearningIntent)["model_learning_intent"] == ModelLearningIntent | None
    assert get_type_hints(ports.LearningCandidate)["skill_gap_report"] == SkillGapReport | None
    assert get_type_hints(ports.LearningCandidate)["tool_need_report"] == ToolNeedReport | None

def test_phase7_learning_ports_do_not_execute_learning_or_generate_skills():
    text = Path(ports.__file__).read_text(encoding="utf-8")
    forbidden = ["open(", "read_text(", "write_text(", "LearningExecutor", "SkillManager", "CapabilityPort", "AbilityPackagePort"]
    assert [item for item in forbidden if item in text] == []
