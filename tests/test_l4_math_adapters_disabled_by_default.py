from __future__ import annotations

from tiangong_kernel.l4_action_grounding.llm_judge_adapter import LLMJudgeAdapter
from tiangong_kernel.l4_action_grounding.math_model_adapter import (
    BaseMathModelAdapter,
    DeterministicLocalScoreAdapter,
    ExternalModelAdapter,
    FallbackAdapter,
    ReplayAdapter,
    ShadowAdapter,
)
from tiangong_kernel.l4_action_grounding.python_math_adapter import PythonMathAdapter
from tiangong_kernel.l4_action_grounding.statistics_adapter import StatisticsAdapter


def test_l4_math_adapters_are_disabled_by_default() -> None:
    adapters = (
        BaseMathModelAdapter(),
        DeterministicLocalScoreAdapter(),
        ExternalModelAdapter(),
        ReplayAdapter(),
        ShadowAdapter(),
        FallbackAdapter(),
        PythonMathAdapter(),
        StatisticsAdapter(),
        LLMJudgeAdapter(),
    )

    for adapter in adapters:
        assert adapter.disabled_by_default is True
        assert adapter.requires_l5_permit is True
        assert adapter.adapter_descriptor.enabled_by_default is False
        assert adapter.adapter_descriptor.production_enabled is False


def test_l4_math_adapter_invocations_return_disabled_refs() -> None:
    for adapter in (BaseMathModelAdapter(), PythonMathAdapter(), StatisticsAdapter(), LLMJudgeAdapter()):
        invocation = adapter.invoke() if hasattr(adapter, "invoke") else adapter.run_disabled()
        assert invocation.disabled is True
        assert invocation.dry_run is True
        assert invocation.no_op is True
        assert invocation.real_calculation_performed is False
        assert invocation.external_call_performed is False
        assert invocation.action_enabled is False
