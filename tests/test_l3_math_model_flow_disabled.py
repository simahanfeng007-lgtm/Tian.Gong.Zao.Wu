from __future__ import annotations

from tiangong_kernel.l3_orchestration.math_model_engine_flow import (
    ConfidenceSynthesisFlow,
    DriftDetectionFlow,
    MathFeatureExtractionFlow,
    MathScoreAggregationFlow,
    MathScoringFlow,
    ModelCalibrationFlow,
    ModelConflictFlow,
)


def test_l3_math_model_flows_are_disabled_safe_and_advisory_only() -> None:
    flows = (
        MathFeatureExtractionFlow(),
        MathScoringFlow(),
        MathScoreAggregationFlow(),
        ConfidenceSynthesisFlow(),
        ModelConflictFlow(),
        ModelCalibrationFlow(),
        DriftDetectionFlow(),
    )

    for flow in flows:
        assert flow.request_only is True
        assert flow.advisory_only is True
        assert flow.evidence_only is True
        assert flow.disabled_safe is True
        assert flow.no_final_decision is True
        assert flow.no_tool_action is True
