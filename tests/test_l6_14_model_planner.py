from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tiangong_agent_runtime.model_planner import ModelPlanner
from tiangong_agent_runtime.plan_schema import PlanValidationError, validate_and_build_plan
from tiangong_agent_runtime.planner_mode import PlannerMode
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.model_client_mock import MockModelClient
from tiangong_agent_shell.model_client_port import ChatResult
from tiangong_agent_shell.tool_bridge import ToolExecutionMode

ROOT = Path(__file__).resolve().parents[1]


class JsonPlanClient:
    provider = "json-plan"

    def __init__(self, payload: object) -> None:
        self.payload = payload

    def chat(self, messages: list[dict[str, str]], config: ModelConfig) -> ChatResult:  # noqa: ARG002
        return ChatResult(content=json.dumps(self.payload, ensure_ascii=False), provider=self.provider, model="planner")


class InvalidPlanClient:
    provider = "invalid-plan"

    def chat(self, messages: list[dict[str, str]], config: ModelConfig) -> ChatResult:  # noqa: ARG002
        return ChatResult(content='{"steps":[{"tool_name":"shell","arguments":{"command":"rm -rf /"}}]}', provider=self.provider, model="planner")


def test_model_planner_accepts_json_plan_and_builds_tool_invocations() -> None:
    planner = ModelPlanner()
    result = planner.build_plan(
        "读取 README 后打包",
        model_config=ModelConfig(provider="mock", model="mock-model"),
        model_client=JsonPlanClient(
            {
                "steps": [
                    {"tool_name": "read_file", "arguments": {"path": "README.md"}, "reason": "读取说明"},
                    {"tool_name": "create_zip_package", "arguments": {"source": ".", "target": "dist/final.zip"}},
                ]
            }
        ),
    )
    assert result.ok
    assert [step.tool_name for step in result.plan] == ["read_file", "create_zip_package"]
    assert result.plan[0].arguments["path"] == "README.md"


def test_plan_validator_rejects_unknown_tool_absolute_path_and_shell_like_payload() -> None:
    with pytest.raises(PlanValidationError) as exc_info:
        validate_and_build_plan(
            {
                "steps": [
                    {"tool_name": "shell", "arguments": {"command": "rm -rf /"}},
                    {"tool_name": "read_file", "arguments": {"path": "/etc/passwd"}},
                ]
            }
        )
    codes = {issue.code for issue in exc_info.value.issues}
    assert "tool_not_allowed" in codes
    assert "unsafe_path" in codes


def test_runtime_model_suggest_plan_executes_through_governed_chain(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("hello", encoding="utf-8")
    runtime = RuntimeEntry()
    result = runtime.run_text(
        "请检查这个项目，读取 README，然后打包交付",
        workspace=tmp_path,
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        planner_mode=PlannerMode.MODEL_SUGGEST,
        model_config=ModelConfig(provider="mock", model="mock-model"),
        model_client=MockModelClient(),
        max_steps=10,
    )
    assert result.has_plan
    assert result.planner_result is not None and result.planner_result.ok
    assert any(step.tool_name == "read_file" for step in result.plan)
    assert result.results
    assert all(event["tool_name"] != "model_chat" for event in result.audit_events)
    assert (tmp_path / "dist" / "model_planner_demo.zip").exists()


def test_model_required_invalid_plan_does_not_execute_or_fallback(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    result = runtime.run_text(
        "请执行 shell 删除",
        workspace=tmp_path,
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        planner_mode=PlannerMode.MODEL_REQUIRED,
        model_config=ModelConfig(provider="mock", model="mock-model"),
        model_client=InvalidPlanClient(),
    )
    assert not result.has_plan
    assert result.results == []
    assert result.planner_result is not None
    assert not result.planner_result.ok
    assert result.projection.status == "planner_failed"


def test_shell_plan_preview_uses_mock_model_planner_without_execution(tmp_path: Path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "run_agent.py",
            "--mock",
            "--tool-mode",
            "runtime_governed",
            "--planner-mode",
            "model_suggest",
            "--workspace",
            str(tmp_path),
        ],
        cwd=ROOT,
        input="/plan 请检查项目并打包\n/exit\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
    )
    assert proc.returncode == 0
    assert '"planner_mode": "model_suggest"' in proc.stdout
    assert '"tool_name": "list_dir"' in proc.stdout
    assert not (tmp_path / "dist" / "model_planner_demo.zip").exists()


def test_shell_model_suggest_once_executes_model_generated_write_plan(tmp_path: Path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "run_agent.py",
            "--mock",
            "--tool-mode",
            "runtime_governed",
            "--planner-mode",
            "model_suggest",
            "--workspace",
            str(tmp_path),
            "--once",
            "请生成文件",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
    )
    assert proc.returncode == 0
    assert "[计划器] 模型计划生成成功" in proc.stdout
    assert "write_workspace_file" in proc.stdout
    assert (tmp_path / "model_planner_demo.txt").exists()
