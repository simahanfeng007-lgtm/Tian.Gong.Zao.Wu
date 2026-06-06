from __future__ import annotations

from pathlib import Path

import pytest

from tiangong_kernel.l3_orchestration.math_model_engine_flow import MathFormulaParameterizationRef


def test_l3_formula_parameterization_is_externalized() -> None:
    ref = MathFormulaParameterizationRef(formula_id="retention-pressure")

    assert ref.externalized is True
    assert ref.formula_profile_ref is None
    assert ref.parameter_snapshot_ref is None
    assert ref.threshold_policy_ref is None

    with pytest.raises(ValueError):
        MathFormulaParameterizationRef(externalized=False)


def test_l3_math_flow_does_not_hardcode_cognitive_formula_names() -> None:
    source = Path("tiangong_kernel/l3_orchestration/math_model_engine_flow.py").read_text(encoding="utf-8")
    forbidden = ("Ebbinghaus", "ACT-R", "Bayes", "Bayesian", "reinforcement_learning_formula")

    assert not any(token in source for token in forbidden)
