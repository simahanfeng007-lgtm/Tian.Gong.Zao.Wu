from pathlib import Path

from tiangong_kernel.l4_action_grounding import (
    CustomFormulaAdapter,
    ExternalScoringAdapter,
    LLMJudgeAdapter,
    LocalModelScoringAdapter,
    MathAdapterDescriptor,
    MathAdapterInvocationRef,
    MathAdapterProtocol,
    ModelEvaluationAdapter,
    OptionalThirdPartyMathAdapterDescriptor,
    PythonMathAdapter,
    StatisticsAdapter,
)


ADAPTER_CLASSES = (
    PythonMathAdapter,
    ExternalScoringAdapter,
    LocalModelScoringAdapter,
    LLMJudgeAdapter,
    StatisticsAdapter,
    CustomFormulaAdapter,
    ModelEvaluationAdapter,
)


def test_l4_math_adapters_are_disabled_by_default_and_require_l5_permit():
    for cls in ADAPTER_CLASSES:
        adapter = cls()
        assert isinstance(adapter, MathAdapterProtocol)
        descriptor = adapter.describe()
        assert isinstance(descriptor, MathAdapterDescriptor)
        assert descriptor.disabled_by_default is True
        assert descriptor.enabled_by_default is False
        assert descriptor.requires_l5_permit is True
        assert descriptor.production_enabled is False
        assert descriptor.performs_real_calculation is False
        assert descriptor.calls_external_service is False
        assert descriptor.turns_score_into_action is False
        assert descriptor.grants_permission is False
        assert descriptor.writes_l2_state is False

        for result in (adapter.dry_run(), adapter.invoke()):
            assert isinstance(result, MathAdapterInvocationRef)
            assert result.disabled is True
            assert result.dry_run is True
            assert result.no_op is True
            assert result.real_calculation_performed is False
            assert result.external_call_performed is False
            assert result.action_enabled is False


def test_l4_optional_third_party_descriptor_names_dependencies_without_importing_them():
    descriptor = OptionalThirdPartyMathAdapterDescriptor().descriptor
    assert descriptor.disabled_by_default is True
    assert descriptor.requires_l5_permit is True
    assert descriptor.optional_dependency_names == ("numpy", "scipy", "sklearn")
    assert descriptor.performs_real_calculation is False


def test_l4_math_adapter_files_have_no_third_party_or_external_call_imports():
    files = (
        Path("tiangong_kernel/l4_action_grounding/math_adapter_protocol.py"),
        Path("tiangong_kernel/l4_action_grounding/math_adapter_descriptor.py"),
        Path("tiangong_kernel/l4_action_grounding/python_math_adapter.py"),
        Path("tiangong_kernel/l4_action_grounding/external_scoring_adapter.py"),
        Path("tiangong_kernel/l4_action_grounding/local_model_scoring_adapter.py"),
        Path("tiangong_kernel/l4_action_grounding/llm_judge_adapter.py"),
        Path("tiangong_kernel/l4_action_grounding/statistics_adapter.py"),
        Path("tiangong_kernel/l4_action_grounding/custom_formula_adapter.py"),
        Path("tiangong_kernel/l4_action_grounding/model_evaluation_adapter.py"),
        Path("tiangong_kernel/l4_action_grounding/optional_third_party_math_adapter_descriptor.py"),
    )
    forbidden = (
        "import numpy",
        "from numpy",
        "import scipy",
        "from scipy",
        "import sklearn",
        "from sklearn",
        "import requests",
        "import subprocess",
        "import socket",
        "open(",
    )
    for file in files:
        source = file.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in source, (file, token)
