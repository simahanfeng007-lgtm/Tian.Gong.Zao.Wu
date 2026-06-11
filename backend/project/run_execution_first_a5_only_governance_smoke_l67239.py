from __future__ import annotations

import tempfile
from pathlib import Path

from tiangong_agent_runtime.execution_policy import ExecutionPolicy, PermitStatus, RiskLevel
from tiangong_agent_runtime.plan_schema import validate_and_build_plan, PlanValidationError
from tiangong_agent_runtime.risk_classifier import RiskClassifier
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.workspace_guard import WorkspaceGuard


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    policy = ExecutionPolicy.default()
    for level in [RiskLevel.A0, RiskLevel.A1, RiskLevel.A2, RiskLevel.A3, RiskLevel.A4]:
        require(policy.dynamic_status(level) is PermitStatus.ALLOWED, f"{level} must auto-allow")
    require(policy.dynamic_status(RiskLevel.A5) is PermitStatus.BLOCKED, "A5 must remain blocked")

    steps = [
        {"tool_name": "safe_command_runner", "arguments": {"command": "npm test", "cwd": "."}},
        {"tool_name": "write_workspace_file", "arguments": {"path": r"C:\\Users\\77571\\Desktop\\demo.txt", "content": "ok"}},
    ] + [
        {"tool_name": "return_analysis", "arguments": {"content": f"step {idx}"}}
        for idx in range(25)
    ]
    plan = validate_and_build_plan({"steps": steps}, max_steps=20)
    require(len(plan) == 27, "planner schema must not enforce old 20-step hard limit")
    require(plan[0].tool_name == "safe_command_runner", "shell/run command should normalize to Code-X safe_command_runner")
    require(plan[0].arguments.get("command") == "npm test", "non-A5 command should pass schema")
    require(plan[1].arguments.get("path", "").startswith("C:"), "absolute Windows path should pass schema")

    try:
        validate_and_build_plan({"steps": [{"tool_name": "safe_command_runner", "arguments": {"command": "rm -rf /"}}]})
    except PlanValidationError as exc:
        require(any(issue.code == "unsafe_a5_command" for issue in exc.issues), "A5 command must still be caught")
    else:
        raise AssertionError("A5 command should fail schema")

    classifier = RiskClassifier()
    risk, _ = classifier.classify(ToolInvocation("write_workspace_file", {"path": r"C:\\Users\\77571\\Desktop\\demo.txt", "content": "ok"}))
    require(risk is not RiskLevel.A5, "absolute write must not become A5 by default")
    risk, _ = classifier.classify(ToolInvocation("unknown_future_tool", {"task": "do work"}))
    require(risk is RiskLevel.A4, "unknown non-A5 tool should be A4, not hard-block A5")
    risk, _ = classifier.classify(ToolInvocation("safe_command_runner", {"command": "rm -rf /"}))
    require(risk is RiskLevel.A5, "destructive command remains A5")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        guard = WorkspaceGuard(root)
        target = root / "Desktop" / "demo.txt"
        resolved = guard.resolve_for_write(str(target))
        require(resolved == target, "absolute path inside host root should be accepted")

    print("PASS L6.72.39 execution-first A5-only governance smoke")


if __name__ == "__main__":
    main()
