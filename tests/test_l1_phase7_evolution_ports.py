import inspect
from dataclasses import is_dataclass
from pathlib import Path
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.learning import EvolutionRef, ImprovementProposalRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l1_ports.model_reflection_ports import ModelEvolutionHint
from tiangong_kernel.l1_ports.port_result import PortResult
from tiangong_kernel.l1_ports.self_iteration_ports import IterationCandidate
from tiangong_kernel.l1_ports.skill_evolution_ports import SkillEvolutionHint
from tiangong_kernel.l1_ports.tool_gap_ports import ToolNeedReport
import tiangong_kernel.l1_ports.evolution_ports as ports

PORT_CLASSES = [ports.EvolutionIntentPort, ports.EvolutionCandidatePort, ports.EvolutionBoundaryPort, ports.EvolutionEvidencePort, ports.EvolutionDecisionHintPort, ports.EvolutionRollbackHintPort, ports.EvolutionContinuityPort]
DATA_CLASSES = [ports.EvolutionIntent, ports.EvolutionCandidate, ports.EvolutionBoundary, ports.EvolutionEvidence, ports.EvolutionDecisionHint, ports.EvolutionRollbackHint, ports.EvolutionContinuity, ports.EvolutionIntentRequest, ports.EvolutionIntentResponse, ports.EvolutionCandidateRequest, ports.EvolutionCandidateResponse, ports.EvolutionBoundaryRequest, ports.EvolutionBoundaryResponse, ports.EvolutionEvidenceRequest, ports.EvolutionEvidenceResponse, ports.EvolutionDecisionHintRequest, ports.EvolutionDecisionHintResponse, ports.EvolutionRollbackHintRequest, ports.EvolutionRollbackHintResponse, ports.EvolutionContinuityRequest, ports.EvolutionContinuityResponse]

def _return_is_result(method):
    return get_origin(get_type_hints(method)["return"]) in {CoreResult, PortResult}

def test_phase7_evolution_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")

def test_phase7_evolution_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))

def test_phase7_evolution_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")

def test_phase7_evolution_reuses_l0_learning_and_phase5_phase6_phase7_objects():
    assert get_type_hints(ports.EvolutionIntent)["evolution_ref"] is EvolutionRef
    assert get_type_hints(ports.EvolutionIntent)["model_evolution_hint"] == ModelEvolutionHint | None
    assert get_type_hints(ports.EvolutionCandidate)["proposal_ref"] == ImprovementProposalRef | None
    assert get_type_hints(ports.EvolutionCandidate)["iteration_candidate"] == IterationCandidate | None
    assert get_type_hints(ports.EvolutionIntent)["tool_need_report"] == ToolNeedReport | None
    assert get_type_hints(ports.EvolutionEvidence)["skill_evolution_hint"] == SkillEvolutionHint | None

def test_phase7_evolution_ports_do_not_execute_evolution_or_stage8_validation():
    text = Path(ports.__file__).read_text(encoding="utf-8")
    forbidden = ["open(", "read_text(", "write_text(", "EvolutionEngine", "CandidatePromotionPort", "EvolutionValidationPort", "RollbackVerificationPort", "CapabilityPort", "AbilityPackagePort"]
    assert [item for item in forbidden if item in text] == []
