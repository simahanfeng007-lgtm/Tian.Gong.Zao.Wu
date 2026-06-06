from pathlib import Path

from tiangong_kernel.l3_orchestration import (
    AdaptationDecisionFlow,
    DefaultHeuristicScoringProfile,
    EvolutionAssessmentFlow,
    ForgettingScoringFlow,
    HealthScoringFlow,
    LearningAssessmentFlow,
    MathFormulaProfileRef,
    MathModelFlowOutputBundle,
    MathModelFlowRecommendation,
    MathModelOrchestrationFlow,
    MemoryScoringFlow,
    RegressionRiskFlow,
    ResourcePressureFlow,
    RiskScoringFlow,
    ScoringFlow,
)
from tiangong_kernel.l3_orchestration.orchestration_math import DEFAULT_HEURISTIC_SCORING_PROFILE


DOMAIN_FLOW_CLASSES = (
    MemoryScoringFlow,
    ForgettingScoringFlow,
    HealthScoringFlow,
    RiskScoringFlow,
    ResourcePressureFlow,
    EvolutionAssessmentFlow,
    RegressionRiskFlow,
    LearningAssessmentFlow,
    AdaptationDecisionFlow,
)


def test_l3_formal_math_flows_are_advisory_only():
    profile = MathFormulaProfileRef(profile_name="future_profile")
    flow = ScoringFlow(formula_profile_ref=profile)
    orchestration_flow = flow.as_orchestration_flow()
    assert orchestration_flow.advisory_only is True
    assert orchestration_flow.formal_engine_path is True
    assert orchestration_flow.legacy_heuristic_path is False
    assert orchestration_flow.writes_l2_state is False
    assert orchestration_flow.bypasses_l5 is False
    assert orchestration_flow.produces_execution_command is False

    output = MathModelFlowOutputBundle(recommendation_refs=(MathModelFlowRecommendation(),))
    declared = MathModelOrchestrationFlow().declare_output(output)
    assert declared.output_bundle.advisory_only is True
    assert declared.output_bundle.writes_l2_state is False
    assert declared.output_bundle.produces_action_request is False


def test_l3_domain_scoring_flows_share_formal_boundary():
    for cls in DOMAIN_FLOW_CLASSES:
        flow = cls()
        assert flow.advisory_only is True
        assert flow.formal_engine_path is True
        assert flow.compatibility_only is False
        assert flow.contains_formula is False
        assert flow.writes_l2_state is False
        assert flow.bypasses_l5 is False
        assert flow.produces_execution_command is False


def test_l3_legacy_heuristic_scoring_is_compatibility_only():
    assert isinstance(DEFAULT_HEURISTIC_SCORING_PROFILE, DefaultHeuristicScoringProfile)
    assert DEFAULT_HEURISTIC_SCORING_PROFILE.compatibility_only is True
    assert DEFAULT_HEURISTIC_SCORING_PROFILE.formal_engine_path is False
    assert DEFAULT_HEURISTIC_SCORING_PROFILE.legacy_marker.compatibility_only is True
    assert DEFAULT_HEURISTIC_SCORING_PROFILE.legacy_marker.formal_engine_path is False


def test_l3_math_flow_files_import_no_upper_layers_and_emit_no_authority_objects():
    files = (
        Path("tiangong_kernel/l3_orchestration/math_formula_profile_ref.py"),
        Path("tiangong_kernel/l3_orchestration/math_model_flow.py"),
        Path("tiangong_kernel/l3_orchestration/scoring_flow.py"),
        Path("tiangong_kernel/l3_orchestration/domain_scoring_flow.py"),
    )
    forbidden_imports = ("tiangong_kernel.l4_", "tiangong_kernel.l5", "tiangong_kernel.l6")
    forbidden_symbols = ("PermissionDecision", "PolicyDecision", "ConfirmationTicket", "LeaseGrant")
    for file in files:
        source = file.read_text(encoding="utf-8")
        for token in forbidden_imports + forbidden_symbols:
            assert token not in source, (file, token)
