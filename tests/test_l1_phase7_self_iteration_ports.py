import inspect
from dataclasses import is_dataclass
from pathlib import Path
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.learning import ImprovementProposalRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l1_ports.learning_ports import LearningCandidate
from tiangong_kernel.l1_ports.model_reflection_ports import ModelIterationHint
from tiangong_kernel.l1_ports.port_result import PortResult
from tiangong_kernel.l1_ports.skill_evolution_ports import SkillIterationHint
from tiangong_kernel.l1_ports.tool_gap_ports import ToolGroupGapReport
import tiangong_kernel.l1_ports.self_iteration_ports as ports

PORT_CLASSES = [ports.IterationCandidatePort, ports.IterationPatchIntentPort, ports.IterationReviewPort, ports.IterationRollbackHintPort, ports.IterationEvidencePort, ports.IterationBoundaryPort]
DATA_CLASSES = [ports.IterationCandidate, ports.IterationPatchIntent, ports.IterationReview, ports.IterationRollbackHint, ports.IterationEvidence, ports.IterationBoundary, ports.IterationCandidateRequest, ports.IterationCandidateResponse, ports.IterationPatchIntentRequest, ports.IterationPatchIntentResponse, ports.IterationReviewRequest, ports.IterationReviewResponse, ports.IterationRollbackHintRequest, ports.IterationRollbackHintResponse, ports.IterationEvidenceRequest, ports.IterationEvidenceResponse, ports.IterationBoundaryRequest, ports.IterationBoundaryResponse]

def _return_is_result(method):
    return get_origin(get_type_hints(method)["return"]) in {CoreResult, PortResult}

def test_phase7_self_iteration_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")

def test_phase7_self_iteration_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))

def test_phase7_self_iteration_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")

def test_phase7_self_iteration_reuses_learning_model_and_skill_gap_objects():
    assert get_type_hints(ports.IterationCandidate)["proposal_ref"] == ImprovementProposalRef | None
    assert get_type_hints(ports.IterationCandidate)["learning_candidate"] == LearningCandidate | None
    assert get_type_hints(ports.IterationCandidate)["model_iteration_hint"] == ModelIterationHint | None
    assert get_type_hints(ports.IterationCandidate)["skill_iteration_hint"] == SkillIterationHint | None
    assert get_type_hints(ports.IterationEvidence)["tool_group_gap_report"] == ToolGroupGapReport | None

def test_phase7_self_iteration_ports_do_not_generate_patch_or_rollback():
    text = Path(ports.__file__).read_text(encoding="utf-8")
    forbidden = ["open(", "read_text(", "write_text(", "IterationRuntime", "LearningExecutor", "CapabilityPort", "AbilityPackagePort"]
    assert [item for item in forbidden if item in text] == []
