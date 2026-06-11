from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path

from tiangong_agent_runtime.adapters.readonly_file_adapter import file_sha256_adapter
from tiangong_agent_runtime.code_x_runtime_adapters import _summary_from_payload
from tiangong_agent_runtime.plan_bridge import PlanBridge
from tiangong_agent_runtime.plan_schema import validate_and_build_plan
from tiangong_agent_runtime.risk_classifier import RiskClassifier
from tiangong_agent_runtime.runtime_entry import RuntimeEntry, build_default_registry
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.tool_result import ToolResultStatus
from tiangong_agent_runtime.turn_context import TurnContext
from tiangong_agent_runtime.execution_policy import RiskLevel


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    bridge = PlanBridge()

    sha_plan = bridge.build_plan("Work task: compute SHA256 of `delivery.zip` and report the digest.")
    require(len(sha_plan) == 1, f"unexpected sha plan length: {sha_plan}")
    require(sha_plan[0].tool_name == "file_sha256", f"sha task routed to {sha_plan[0].tool_name}")
    require(sha_plan[0].arguments.get("path") == "delivery.zip", "sha path was not preserved")
    validated_sha = validate_and_build_plan({"steps": [{"tool_name": sha_plan[0].tool_name, "arguments": sha_plan[0].arguments}]})
    require(validated_sha[0].tool_name == "file_sha256", "schema rejected file_sha256")

    calc_plan = bridge.build_plan("Work task: run a local Python calculation for 19*23 and report only the result.")
    require(len(calc_plan) == 1, f"unexpected calc plan length: {calc_plan}")
    require(calc_plan[0].tool_name == "safe_command_runner", f"calc task routed to {calc_plan[0].tool_name}")
    command = str(calc_plan[0].arguments.get("command") or "")
    require("print(19*23)" in command, f"calc command missing expression: {command}")
    validated_calc = validate_and_build_plan({"steps": [{"tool_name": calc_plan[0].tool_name, "arguments": calc_plan[0].arguments}]})
    require(validated_calc[0].tool_name == "safe_command_runner", "schema rejected safe_command_runner calc")
    require(isinstance(validated_calc[0].arguments.get("command"), list), "safe_command_runner argv command must remain a list")

    write_plan = bridge.build_plan("write linyuanzhe_round14_task_probe/roundtrip.txt :: round14_task_execution_ok")
    require(write_plan and write_plan[0].tool_name == "write_workspace_file", f"write task routed to {write_plan[0].tool_name if write_plan else '<empty>'}")

    hinted_write = bridge.build_plan("write probe.txt :: ok\n\n[桌面端主机文件访问提示]\n- access_scope=custom_root")
    require(hinted_write and hinted_write[0].arguments.get("content") == "ok", "write parser must not persist appended host hint")

    read_plan = bridge.build_plan("read linyuanzhe_round14_task_probe/roundtrip.txt")
    require(read_plan and read_plan[0].tool_name == "read_file", f"read task routed to {read_plan[0].tool_name if read_plan else '<empty>'}")

    safe_summary = _summary_from_payload({"result": {"stdout": "437\n", "stderr": "", "exit_code": 0}}, "safe_command_runner")
    require(safe_summary.strip() == "437", "safe_command_runner summary must expose safe stdout")

    risk, _ = RiskClassifier().classify(ToolInvocation("file_sha256", {"path": "delivery.zip"}))
    require(risk is RiskLevel.A1, "file_sha256 must stay A1")

    registry = build_default_registry()
    require(registry.get("file_sha256") is not None, "file_sha256 missing from default registry")

    original_cwd = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp_runtime:
        os.chdir(tmp_runtime)
        try:
            runtime = RuntimeEntry(registry=registry)
            runtime_plan, runtime_planner = runtime._build_plan_for_text(
                "Work task: run a local Python calculation for 19*23 and report only the result.",
                planner_mode="model_suggest",
                model_config=None,
                model_client=None,
                max_steps=8,
            )
        finally:
            os.chdir(original_cwd)
    require(runtime_planner is not None and runtime_planner.source == "deterministic_preflight", "deterministic preflight did not bypass model planning")
    require(runtime_plan and runtime_plan[0].tool_name == "safe_command_runner", "runtime preflight calc plan wrong")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        sample = root / "delivery.zip"
        payload = b"round14 task execution planning smoke\n"
        sample.write_bytes(payload)
        ctx = TurnContext.create("compute SHA256 of delivery.zip", workspace=root)
        result = file_sha256_adapter(ToolInvocation("file_sha256", {"path": "delivery.zip"}), ctx)
        require(result.status is ToolResultStatus.OK, f"file_sha256 adapter failed: {result.output_summary}")
        require(result.data.get("sha256") == hashlib.sha256(payload).hexdigest(), "sha256 digest mismatch")
        require(result.data.get("bytes") == len(payload), "sha256 byte count mismatch")

    print("PASS L6.73.8 Round14 task execution planning smoke")


if __name__ == "__main__":
    main()
