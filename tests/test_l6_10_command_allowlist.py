from __future__ import annotations

from tiangong_agent_runtime.risk_classifier import RiskClassifier
from tiangong_agent_runtime.execution_policy import RiskLevel
from tiangong_agent_runtime.tool_invocation import ToolInvocation


def test_dangerous_command_is_a5() -> None:
    risk, _ = RiskClassifier().classify(
        ToolInvocation("run_python_quality_check", {"command": "rm -rf /", "target": "."})
    )
    assert risk is RiskLevel.A5


def test_compileall_is_a3() -> None:
    risk, _ = RiskClassifier().classify(
        ToolInvocation("run_python_quality_check", {"command": "compileall", "target": "."})
    )
    assert risk is RiskLevel.A3
