from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tiangong_agent_runtime.context_memory_bridge import ContextMemoryBridge
from tiangong_agent_runtime.model_planner import ModelPlanner
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.model_client_port import ChatResult
from tiangong_agent_shell.tool_bridge import ToolExecutionMode

ROOT = Path(__file__).resolve().parents[1]


class RecordingPlanClient:
    provider = "recording-plan"

    def __init__(self) -> None:
        self.last_messages: list[dict[str, str]] = []

    def chat(self, messages: list[dict[str, str]], config: ModelConfig) -> ChatResult:  # noqa: ARG002
        self.last_messages = messages
        return ChatResult(
            content=json.dumps({"steps": [{"tool_name": "list_dir", "arguments": {"path": "."}}]}, ensure_ascii=False),
            provider=self.provider,
            model="planner",
        )


def test_context_memory_records_runtime_runs_without_full_content_or_key(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    result = runtime.run_text(
        "write demo.txt :: hello sk-secret-123456",
        workspace=tmp_path,
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
    )
    assert result.results
    snapshot = runtime.context_snapshot()
    assert snapshot["session_records"] == 1
    text = json.dumps(snapshot, ensure_ascii=False)
    assert "write_workspace_file" in text
    assert "sk-secret-123456" not in text


def test_context_memory_export_and_reset(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    runtime.run_text("write demo.txt :: hello", workspace=tmp_path, tool_mode=ToolExecutionMode.RUNTIME_GOVERNED)
    exported = runtime.export_context_json(tmp_path / "ctx" / "context.json")
    assert exported.exists()
    payload = json.loads(exported.read_text(encoding="utf-8"))
    assert payload["schema"] == "tiangong.l6_15.context_memory.v1"
    assert len(payload["records"]) == 1
    runtime.reset_context_memory()
    assert runtime.context_snapshot()["session_records"] == 0


def test_model_planner_receives_context_hint_but_only_executes_validated_plan(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    runtime.run_text("write known.txt :: previous", workspace=tmp_path, tool_mode=ToolExecutionMode.RUNTIME_GOVERNED)
    client = RecordingPlanClient()
    result = runtime.run_text(
        "根据上次结果继续检查",
        workspace=tmp_path,
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        planner_mode="model_suggest",
        model_config=ModelConfig(provider="mock", model="mock-model"),
        model_client=client,
    )
    assert result.has_plan
    user_message = client.last_messages[-1]["content"]
    assert "最近运行上下文摘要" in user_message
    assert "write_workspace_file" in user_message
    assert result.plan[0].tool_name == "list_dir"


def test_cli_context_commands_show_and_export_context(tmp_path: Path) -> None:
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
        input="/run write demo.txt :: hello\n/context\n/context-save ctx.json\n/context-reset\n/context\n/exit\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=25,
    )
    assert proc.returncode == 0, proc.stderr
    assert "session_records" in proc.stdout
    assert "上下文摘要已导出" in proc.stdout
    assert "上下文摘要已清空" in proc.stdout
    assert (tmp_path / "ctx.json").exists()


def test_context_memory_bridge_drops_old_records(tmp_path: Path) -> None:
    bridge = ContextMemoryBridge(max_records=2)
    runtime = RuntimeEntry()
    for idx in range(3):
        result = runtime.run_text(f"write f{idx}.txt :: x", workspace=tmp_path, tool_mode=ToolExecutionMode.RUNTIME_GOVERNED)
        bridge.observe_run(result)
    assert len(bridge.records) == 2
