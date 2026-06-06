from __future__ import annotations

import pytest

from tiangong_kernel.l3_orchestration.math_model_engine_flow import ModelShadowFlow


def test_l3_math_model_shadow_flow_never_affects_main_path() -> None:
    flow = ModelShadowFlow()

    assert flow.affects_main_path is False
    assert flow.advisory_only is True

    with pytest.raises(ValueError):
        ModelShadowFlow(affects_main_path=True)
