import inspect
from dataclasses import is_dataclass
from pathlib import Path
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.learning import LearningRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l1_ports.learning_ports import LearningCandidate, LearningIntent
from tiangong_kernel.l1_ports.model_feedback_ports import ModelLearningIntent
from tiangong_kernel.l1_ports.port_result import PortResult
from tiangong_kernel.l1_ports.skill_evolution_ports import SkillEvolutionHint
from tiangong_kernel.l1_ports.tool_gap_ports import SkillGapReport, ToolNeedReport
import tiangong_kernel.l1_ports.self_learning_ports as ports

PORT_CLASSES = [ports.SelfLearningCandidatePort, ports.KnowledgeIngestionIntentPort, ports.SkillLearningHintPort, ports.SelfLearningEvidencePort, ports.SelfLearningReviewPort, ports.SelfLearningBoundaryPort]
DATA_CLASSES = [ports.SelfLearningCandidate, ports.KnowledgeIngestionIntent, ports.SkillLearningHint, ports.SelfLearningEvidence, ports.SelfLearningReview, ports.SelfLearningBoundary, ports.SelfLearningCandidateRequest, ports.SelfLearningCandidateResponse, ports.KnowledgeIngestionIntentRequest, ports.KnowledgeIngestionIntentResponse, ports.SkillLearningHintRequest, ports.SkillLearningHintResponse, ports.SelfLearningEvidenceRequest, ports.SelfLearningEvidenceResponse, ports.SelfLearningReviewRequest, ports.SelfLearningReviewResponse, ports.SelfLearningBoundaryRequest, ports.SelfLearningBoundaryResponse]

def _return_is_result(method):
    return get_origin(get_type_hints(method)["return"]) in {CoreResult, PortResult}

def test_phase7_self_learning_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")

def test_phase7_self_learning_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))

def test_phase7_self_learning_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")

def test_phase7_self_learning_reuses_learning_phase5_and_phase6_objects():
    assert get_type_hints(ports.SelfLearningCandidate)["learning_intent"] == LearningIntent | None
    assert get_type_hints(ports.SelfLearningCandidate)["learning_candidate"] == LearningCandidate | None
    assert get_type_hints(ports.SelfLearningCandidate)["skill_gap_report"] == SkillGapReport | None
    assert get_type_hints(ports.SelfLearningCandidate)["tool_need_report"] == ToolNeedReport | None
    assert get_type_hints(ports.KnowledgeIngestionIntent)["learning_ref"] is LearningRef
    assert get_type_hints(ports.SkillLearningHint)["skill_evolution_hint"] == SkillEvolutionHint | None

def test_phase7_self_learning_ports_do_not_execute_self_learning():
    text = Path(ports.__file__).read_text(encoding="utf-8")
    forbidden = ["open(", "read_text(", "write_text(", "LearningExecutor", "PluginHost", "CapabilityPort", "AbilityPackagePort"]
    assert [item for item in forbidden if item in text] == []
