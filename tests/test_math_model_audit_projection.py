from __future__ import annotations

import pytest

from tiangong_kernel.l3_orchestration.math_model_engine_flow import ModelAuditProjectionFlow


def test_math_model_audit_projection_is_not_audit_write() -> None:
    flow = ModelAuditProjectionFlow()

    assert flow.evidence_only is True
    assert flow.audit_write_performed is False
    assert flow.no_tool_action is True

    with pytest.raises(ValueError):
        ModelAuditProjectionFlow(audit_write_performed=True)
