from __future__ import annotations

from inspect import isabstract

import pytest

from tiangong_kernel.l1_ports.math_engine_contract_ports import (
    CalibrationReport,
    ConfidenceValue,
    DriftSignal,
    FeatureExtractionPort,
    FeatureKey,
    FeatureSnapshot,
    FeatureValue,
    MathModelDefinition,
    MathModelDefinitionPort,
    MathModelDefinitionRequest,
    MathModelId,
    MathModelVersion,
    ModelCalibrationPort,
    ModelConflictPort,
    ModelEvidencePort,
    ModelEvaluationPort,
    ModelGovernancePort,
    ModelGovernanceStatus,
    ModelInputEnvelope,
    ModelReplayPort,
    ModelReplayRequest,
    ModelReplayResult,
    ModelRunId,
    ModelShadowPort,
    ModelTelemetryPort,
    ModelTelemetryRecord,
    ScoreEvidence,
    ScoreResult,
    ScoreValue,
    UncertaintyValue,
)
from tiangong_kernel.l1_ports.math_model_ports import ScoringPort


def test_l1_math_model_value_objects_are_contract_only() -> None:
    model_id = MathModelId("memory_retention")
    model_version = MathModelVersion("0.1")
    run_id = ModelRunId("run-001")
    feature_key = FeatureKey("recency")
    feature_value = FeatureValue(feature_key=feature_key, numeric_value=0.4)
    feature_snapshot = FeatureSnapshot(feature_values=(feature_value,))
    envelope = ModelInputEnvelope(model_id=model_id, model_version=model_version)
    score = ScoreResult(score=ScoreValue(0.7), confidence=ConfidenceValue(0.8), uncertainty=UncertaintyValue(0.2))
    evidence = ScoreEvidence(feature_snapshot_hash=feature_snapshot.feature_snapshot_hash)
    telemetry = ModelTelemetryRecord(latency_ms=0.0, fallback_used=True)

    assert run_id.value == "run-001"
    assert envelope.model_id == model_id
    assert score.advisory_only is True
    assert score.authority_result is False
    assert evidence.evidence_items == ()
    assert telemetry.fallback_used is True


def test_l1_math_model_guards_reject_authority_or_runtime_mutation() -> None:
    with pytest.raises(ValueError):
        ScoreValue(1.1)
    with pytest.raises(ValueError):
        ScoreResult(advisory_only=False)
    with pytest.raises(ValueError):
        ScoreResult(authority_result=True)
    with pytest.raises(ValueError):
        CalibrationReport(report_only=False)
    with pytest.raises(ValueError):
        CalibrationReport(changes_runtime_policy=True)
    with pytest.raises(ValueError):
        DriftSignal(signal_only=False)
    with pytest.raises(ValueError):
        ModelReplayRequest(request_only=False)
    with pytest.raises(ValueError):
        ModelReplayResult(result_only=False)
    with pytest.raises(ValueError):
        ModelGovernanceStatus(status_only=False)


def test_l1_math_model_definition_remains_disabled_by_default() -> None:
    definition = MathModelDefinition(model_id=MathModelId("risk_model"), model_name="Risk Model")
    request = MathModelDefinitionRequest(model_id=definition.model_id)

    assert request.request_only is True
    assert definition.default_disabled is True
    assert definition.definition_only is True
    assert "disabled" in definition.allowed_runtime_modes

    with pytest.raises(ValueError):
        MathModelDefinition(model_id=MathModelId("risk_model"), model_name="Risk Model", default_disabled=False)
    with pytest.raises(ValueError):
        MathModelDefinition(model_id=MathModelId("risk_model"), model_name="Risk Model", definition_only=False)


def test_l1_math_model_ports_are_abstract_protocols() -> None:
    ports = (
        MathModelDefinitionPort,
        FeatureExtractionPort,
        ModelEvaluationPort,
        ModelCalibrationPort,
        ModelEvidencePort,
        ModelTelemetryPort,
        ModelGovernancePort,
        ModelReplayPort,
        ModelShadowPort,
        ModelConflictPort,
        ScoringPort,
    )

    assert all(isabstract(port) for port in ports)
    with pytest.raises(TypeError):
        MathModelDefinitionPort()
