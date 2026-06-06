from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tiangong_agent_runtime.execution_chain_freeze import (
    FORBIDDEN_EXECUTION_CHANNELS,
    L6_37_SCHEMA,
    REQUIRED_REPORT_FLAGS,
    build_default_execution_chain_contract,
    build_execution_chain_freeze_report,
)
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_shell.tool_bridge import ToolExecutionMode

ROOT = Path(__file__).resolve().parents[1]


def _workspace(tmp_path: Path) -> Path:
    (tmp_path / "README.md").write_text("# demo\n", encoding="utf-8")
    return tmp_path


def test_l6_37_default_contract_freezes_single_governed_execution_chain() -> None:
    contract = build_default_execution_chain_contract().public_dict()
    assert contract["schema"] == L6_37_SCHEMA
    assert contract["status"] == "frozen"
    assert contract["no_second_runtime"] is True
    assert contract["no_direct_tool_release"] is True
    assert contract["no_kernel_mutation"] is True
    assert contract["future_systems_must_use_contract"] is True
    assert "PlannerExecutionController" in contract["governed_chain"]
    assert "LongChainRunner" in contract["governed_chain"]
    assert "ExecutionSpine" in contract["governed_chain"]
    assert set(REQUIRED_REPORT_FLAGS).issubset(set(contract["required_report_flags"]))
    assert set(FORBIDDEN_EXECUTION_CHANNELS).issubset(set(contract["forbidden_execution_channels"]))


def test_l6_37_freeze_report_ready_after_planner_execution(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    runtime.execute_plan(
        [ToolInvocation("read_file", {"path": "README.md"}), ToolInvocation("return_analysis", {"content": "ok"})],
        workspace=_workspace(tmp_path),
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps=4,
    )
    report = runtime.execution_chain_freeze_snapshot()
    assert report["schema"] == L6_37_SCHEMA
    assert report["status"] == "frozen"
    assert report["ready"] is True
    assert report["issues"] == []
    assert report["l6_36_ready"] is True
    assert report["source_execution_status"] == "completed"
    assert report["contract"]["status"] == "frozen"
    assert report["can_accept_future_system_mounts"] is True
    assert all(report["checked_report_flags"].values())


def test_l6_37_freeze_report_not_ready_without_execution_report() -> None:
    report = build_execution_chain_freeze_report({}).public_dict()
    assert report["schema"] == L6_37_SCHEMA
    assert report["status"] == "not_ready"
    assert report["ready"] is False
    assert "missing_planner_execution_report" in report["issues"]
    assert "l6_36_quality_recovery_replay_not_ready" in report["issues"]


def test_l6_37_freeze_report_detects_second_runtime_or_direct_adapter_flag(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    runtime.execute_plan([ToolInvocation("return_analysis", {"content": "ok"})], workspace=_workspace(tmp_path), tool_mode=ToolExecutionMode.RUNTIME_GOVERNED)
    payload = runtime.planner_execution_snapshot()
    payload["no_parallel_runtime"] = False
    payload["no_direct_adapter_call"] = False
    report = build_execution_chain_freeze_report(payload).public_dict()
    assert report["ready"] is False
    assert "report_flag_not_true:no_parallel_runtime" in report["issues"]
    assert "report_flag_not_true:no_direct_adapter_call" in report["issues"]


def test_l6_37_contract_export_and_markdown(tmp_path: Path) -> None:
    contract = build_default_execution_chain_contract()
    path = contract.export_json(tmp_path / "contract.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema"] == L6_37_SCHEMA
    text = contract.markdown_report()
    assert "执行链冻结契约" in text
    assert "禁止第二执行通道" in text


def test_l6_37_runtime_export_freeze_report(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    runtime.execute_plan([ToolInvocation("return_code", {"content": "print('ok')"})], workspace=_workspace(tmp_path), tool_mode=ToolExecutionMode.RUNTIME_GOVERNED)
    path = runtime.export_execution_chain_freeze_json(tmp_path / "freeze.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema"] == L6_37_SCHEMA
    assert payload["ready"] is True
    assert payload["contract"]["system_mount_contract"]["must_enter"] == "PlannerExecutionController / RuntimeEntry façade"


def test_l6_37_cli_shows_and_exports_execution_chain_freeze(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# demo\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "run_agent.py", "--mock", "--tool-mode", "runtime_governed", "--workspace", str(tmp_path)],
        cwd=ROOT,
        input="/planner-execute read README.md\n/execution-chain-freeze\n/execution-chain-freeze-save freeze.json\n/execution-chain-contract-save contract.json\n/exit\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "L6.37 执行链冻结验收报告已导出" in proc.stdout
    freeze = json.loads((tmp_path / "freeze.json").read_text(encoding="utf-8"))
    contract = json.loads((tmp_path / "contract.json").read_text(encoding="utf-8"))
    assert freeze["schema"] == L6_37_SCHEMA
    assert freeze["ready"] is True
    assert contract["schema"] == L6_37_SCHEMA
