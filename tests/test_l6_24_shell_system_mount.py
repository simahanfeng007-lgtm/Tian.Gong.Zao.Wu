from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tiangong_agent_runtime.plan_bridge import PlanBridge
from tiangong_agent_runtime.plan_schema import validate_and_build_plan
from tiangong_agent_runtime.risk_classifier import RiskClassifier
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.shell_system_mount import ShellSystemMountBridge, discover_runtime_module_files
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.tool_result import ToolResultStatus
from tiangong_agent_runtime.execution_policy import RiskLevel
from tiangong_agent_shell.tool_bridge import ToolExecutionMode

ROOT = Path(__file__).resolve().parents[1]


def test_l6_24_empty_bridge_is_shell_only() -> None:
    bridge = ShellSystemMountBridge()
    snapshot = bridge.public_dict()
    assert snapshot["schema"] == "tiangong.l6_24.shell_system_mount.v1"
    assert snapshot["status"] == "empty"


def test_l6_24_builds_18_shell_slots_from_installed_runtime() -> None:
    runtime = RuntimeEntry()
    report = runtime.shell_mount.build(
        available_tools=runtime.registry.names(),
        available_modules=discover_runtime_module_files(),
        notes="看已装内容，做壳装系统，不污染内核。",
    )
    payload = report.public_dict()
    assert payload["schema"] == "tiangong.l6_24.shell_system_mount.v1"
    assert payload["status"] == "shell_mount_ready"
    assert payload["system_count"] == 18
    assert len(payload["systems"]) == 18
    assert payload["execution_first"] is True
    assert payload["shell_only"] is True
    assert payload["kernel_pollution_guard"] is True
    assert payload["modifies_kernel"] is False
    assert payload["registers_formal_tool"] is False
    assert payload["releases_tool_handle"] is False
    assert payload["activates_skill"] is False
    assert payload["bypasses_governance"] is False
    by_id = {item["system_id"]: item for item in payload["systems"]}
    assert by_id["S02"]["status"] == "active_shell_mounted"
    assert "tool:scan_project" in by_id["S02"]["installed_evidence"]
    assert by_id["S03"]["status"] == "active_shell_mounted"
    assert "tool:write_workspace_file" in by_id["S03"]["installed_evidence"]
    assert by_id["S06"]["status"] == "active_shell_mounted"
    assert by_id["S16"]["status"] == "reserved_shell_slot"
    assert all(item["shell_only"] is True for item in payload["systems"])
    assert all(item["kernel_mutation_allowed"] is False for item in payload["systems"])


def test_l6_24_runtime_builds_shell_mount_without_formal_activation(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    result = runtime.run_shell_mount_build(
        workspace=tmp_path,
        notes="18 个系统全部按外壳挂载，不注册正式工具。",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
    )
    assert result.results[-1].status is ToolResultStatus.OK
    snapshot = runtime.shell_mount_snapshot()
    assert snapshot["schema"] == "tiangong.l6_24.shell_system_mount.v1"
    assert snapshot["system_count"] == 18
    assert snapshot["active_shell_systems"] >= 15
    assert snapshot["reserved_shell_systems"] >= 1
    assert snapshot["modifies_kernel"] is False
    assert snapshot["registers_formal_tool"] is False


def test_l6_24_tool_is_a2_and_registered() -> None:
    runtime = RuntimeEntry()
    names = {tool.name: tool.default_risk for tool in runtime.available_tools()}
    assert names["build_shell_system_mount"] == "A2"
    risk, reason = RiskClassifier().classify(ToolInvocation("build_shell_system_mount", {"notes": "壳装"}))
    assert risk is RiskLevel.A2
    assert "L6.24" in reason
    assert "不改内核" in reason


def test_l6_24_plan_bridge_and_schema_allow_shell_mount() -> None:
    plan = PlanBridge().build_plan("壳装系统 18个系统根据已装内容挂载")
    assert [step.tool_name for step in plan] == ["build_shell_system_mount"]
    built = validate_and_build_plan(
        {
            "steps": [
                {
                    "tool_name": "build_shell_system_mount",
                    "arguments": {"notes": "十八系统壳装，不污染内核。"},
                }
            ]
        }
    )
    assert built[0].tool_name == "build_shell_system_mount"
    assert "十八系统" in built[0].arguments["notes"]


def test_l6_24_cli_shell_mount_build_and_export(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            "run_agent.py",
            "--mock",
            "--tool-mode",
            "runtime_governed",
            "--workspace",
            str(tmp_path),
        ],
        cwd=ROOT,
        input="/shell-mount-build 看已装内容，做十八系统壳装\n/shell-mount\n/shell-mount-save shell_mount.json\n/exit\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "十八系统壳装" in proc.stdout
    exported = json.loads((tmp_path / "shell_mount.json").read_text(encoding="utf-8"))
    assert exported["schema"] == "tiangong.l6_24.shell_system_mount.v1"
    assert exported["system_count"] == 18
    assert exported["shell_only"] is True
    assert exported["modifies_kernel"] is False
    assert exported["registers_formal_tool"] is False


def test_l6_24_runtime_does_not_pollute_kernel_import_direction() -> None:
    kernel_root = ROOT / "tiangong_kernel"
    forbidden = ["shell_system_mount", "build_shell_system_mount", "ShellSystemMountBridge", "/shell-mount"]
    offenders: list[str] = []
    for path in kernel_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)}::{token}")
    assert offenders == []
