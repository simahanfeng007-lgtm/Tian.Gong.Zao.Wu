import inspect
from dataclasses import FrozenInstanceError, is_dataclass
from pathlib import Path

import pytest

import tiangong_kernel.l1_ports as l1_ports
from tiangong_kernel.l1_ports import (
    AdaptationDecisionPort,
    AdaptationDecisionRequest,
    AdaptationDecisionResponse,
    DecayModelPort,
    DecayModelRequest,
    DecayModelResponse,
    EvolutionAssessmentPort,
    EvolutionAssessmentRequest,
    EvolutionAssessmentResponse,
    ForgettingModelPort,
    ForgettingModelRequest,
    ForgettingModelResponse,
    HealthModelPort,
    HealthModelRequest,
    HealthModelResponse,
    HomeostasisModelPort,
    HomeostasisModelRequest,
    HomeostasisModelResponse,
    InterferenceModelPort,
    InterferenceModelRequest,
    InterferenceModelResponse,
    LearningAssessmentPort,
    LearningAssessmentRequest,
    LearningAssessmentResponse,
    MathModelPortBoundary,
    MathematicalModelPort,
    MathematicalModelRequest,
    MathematicalModelResponse,
    MemoryModelPort,
    MemoryModelRequest,
    MemoryModelResponse,
    RegressionRiskModelPort,
    RegressionRiskModelRequest,
    RegressionRiskModelResponse,
    ReinforcementModelPort,
    ReinforcementModelRequest,
    ReinforcementModelResponse,
    ResourcePressureModelPort,
    ResourcePressureModelRequest,
    ResourcePressureModelResponse,
    RetentionModelPort,
    RetentionModelRequest,
    RetentionModelResponse,
    RiskModelPort,
    RiskModelRequest,
    RiskModelResponse,
    ScoringPort,
    ScoringRequest,
    ScoringResponse,
)


PORT_CLASSES = (
    MathematicalModelPort,
    ScoringPort,
    MemoryModelPort,
    ForgettingModelPort,
    RetentionModelPort,
    DecayModelPort,
    ReinforcementModelPort,
    InterferenceModelPort,
    HealthModelPort,
    HomeostasisModelPort,
    RiskModelPort,
    ResourcePressureModelPort,
    EvolutionAssessmentPort,
    RegressionRiskModelPort,
    LearningAssessmentPort,
    AdaptationDecisionPort,
)

DATA_CLASSES = (
    MathModelPortBoundary,
    MathematicalModelRequest,
    MathematicalModelResponse,
    ScoringRequest,
    ScoringResponse,
    MemoryModelRequest,
    MemoryModelResponse,
    ForgettingModelRequest,
    ForgettingModelResponse,
    RetentionModelRequest,
    RetentionModelResponse,
    DecayModelRequest,
    DecayModelResponse,
    ReinforcementModelRequest,
    ReinforcementModelResponse,
    InterferenceModelRequest,
    InterferenceModelResponse,
    HealthModelRequest,
    HealthModelResponse,
    HomeostasisModelRequest,
    HomeostasisModelResponse,
    RiskModelRequest,
    RiskModelResponse,
    ResourcePressureModelRequest,
    ResourcePressureModelResponse,
    EvolutionAssessmentRequest,
    EvolutionAssessmentResponse,
    RegressionRiskModelRequest,
    RegressionRiskModelResponse,
    LearningAssessmentRequest,
    LearningAssessmentResponse,
    AdaptationDecisionRequest,
    AdaptationDecisionResponse,
)


def test_l1_math_ports_are_abstract_and_exported():
    for cls in PORT_CLASSES:
        assert inspect.isabstract(cls), cls.__name__
        assert cls.__name__ in l1_ports.__all__


def test_l1_math_request_response_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls), cls.__name__
        assert hasattr(cls, "__slots__"), cls.__name__
        item = cls()
        with pytest.raises(FrozenInstanceError):
            item.schema_version = "changed"


def test_l1_math_ports_import_no_upper_layers_or_io():
    source = Path("tiangong_kernel/l1_ports/math_model_ports.py").read_text(encoding="utf-8")
    forbidden = (
        "tiangong_kernel.l2_",
        "tiangong_kernel.l3_",
        "tiangong_kernel.l4_",
        "tiangong_kernel.l5",
        "tiangong_kernel.l6",
        "import os",
        "import pathlib",
        "import subprocess",
        "import socket",
        "import requests",
        "open(",
    )
    for token in forbidden:
        assert token not in source
