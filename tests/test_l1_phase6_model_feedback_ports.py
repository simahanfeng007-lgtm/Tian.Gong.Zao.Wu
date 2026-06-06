import inspect
from dataclasses import is_dataclass
from pathlib import Path
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.content import ContentRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l1_ports.port_result import PortResult
from tiangong_kernel.l1_ports.skill_evolution_ports import SkillCorrectionHint
from tiangong_kernel.l1_ports.tool_gap_ports import SkillGapReport, ToolNeedReport
import tiangong_kernel.l1_ports.model_feedback_ports as ports


PORT_CLASSES = [
    ports.ModelFailureFeedbackPort,
    ports.ModelCorrectionHintPort,
    ports.ModelLearningIntentPort,
    ports.ModelToolNeedFeedbackPort,
    ports.ModelSkillGapFeedbackPort,
]
DATA_CLASSES = [
    ports.ModelFailureFeedback,
    ports.ModelCorrectionHint,
    ports.ModelLearningIntent,
    ports.ModelToolNeedFeedback,
    ports.ModelSkillGapFeedback,
    ports.ModelFailureFeedbackRequest,
    ports.ModelFailureFeedbackResponse,
    ports.ModelCorrectionHintRequest,
    ports.ModelCorrectionHintResponse,
    ports.ModelLearningIntentRequest,
    ports.ModelLearningIntentResponse,
    ports.ModelToolNeedFeedbackRequest,
    ports.ModelToolNeedFeedbackResponse,
    ports.ModelSkillGapFeedbackRequest,
    ports.ModelSkillGapFeedbackResponse,
]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase6_model_feedback_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase6_model_feedback_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase6_model_feedback_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase6_model_feedback_reuses_phase5_gap_and_hint_objects():
    assert get_type_hints(ports.ModelLearningIntent)["intent_ref"] is ResourceRef
    assert get_type_hints(ports.ModelLearningIntent)["topic_content_ref"] == ContentRef | None
    assert get_type_hints(ports.ModelCorrectionHint)["existing_hint"] == SkillCorrectionHint | None
    assert get_type_hints(ports.ModelToolNeedFeedback)["tool_need_report"] == ToolNeedReport | None
    assert get_type_hints(ports.ModelSkillGapFeedback)["skill_ref"] == SkillRef | None
    assert get_type_hints(ports.ModelSkillGapFeedback)["skill_gap_report"] == SkillGapReport | None


def test_phase6_model_feedback_does_not_execute_learning_iteration_or_tool_production():
    text = Path(ports.__file__).read_text(encoding="utf-8")
    forbidden = [
        "SelfLearningPort",
        "EvolutionPort",
        "ToolExecutor",
        "ModelExecutor",
        "AbilityPackagePort",
        "CapabilityPort",
        "requests.post",
        "model.call",
        "tool.call",
    ]
    assert [item for item in forbidden if item in text] == []
