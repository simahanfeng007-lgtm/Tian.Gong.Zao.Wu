import importlib


def test_l3_phase1_package_imports_and_exports_core_surface():
    module = importlib.import_module("tiangong_kernel.l3_orchestration")
    required = {
        "OrchestrationIdentity",
        "OrchestrationRequest",
        "OrchestrationContext",
        "OrchestrationStep",
        "OrchestrationPlan",
        "OrchestrationResult",
        "MathFeatureVector",
        "MathObjectiveVector",
        "MathConstraintSet",
        "MathScoreVector",
        "AffectiveWeightInput",
        "DynamicDriveInput",
        "MathEvaluation",
        "MathRecommendation",
        "RouteRanking",
        "StateTransitionAdvice",
    }
    assert required.issubset(set(module.__all__))
    for name in required:
        assert hasattr(module, name), name


def test_l3_phase1_submodules_import_cleanly():
    submodules = (
        "orchestration_identity",
        "orchestration_status",
        "orchestration_request",
        "orchestration_context",
        "orchestration_step",
        "orchestration_plan",
        "orchestration_result",
        "orchestration_transition",
        "orchestration_invariant",
        "orchestration_error",
        "orchestration_serialization",
        "orchestration_math",
        "orchestration_math_input",
        "orchestration_math_result",
    )
    for name in submodules:
        importlib.import_module(f"tiangong_kernel.l3_orchestration.{name}")
