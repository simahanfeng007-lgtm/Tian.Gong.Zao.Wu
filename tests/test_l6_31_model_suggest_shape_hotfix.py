from __future__ import annotations

import json
from pathlib import Path

import pytest

from tiangong_agent_runtime.plan_schema import PlanValidationError, validate_and_build_plan
from tiangong_agent_runtime.planner_mode import PlannerMode
from tiangong_agent_shell.cli_loop import run_runtime_task
from tiangong_agent_shell.composition_root import build_agent_context
from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.model_client_port import ChatResult
from tiangong_agent_shell.tool_bridge import ToolExecutionMode


class ShapeThenFailClient:
    provider = "shape-then-fail"

    def __init__(self) -> None:
        self.planner_calls = 0
        self.chat_messages_seen: list[list[dict[str, str]]] = []

    def chat(self, messages: list[dict[str, str]], config: ModelConfig) -> ChatResult:  # noqa: ARG002
        system_text = "\n".join(str(message.get("content", "")) for message in messages if message.get("role") == "system")
        if "计划生成器" in system_text and "steps" in system_text:
            self.planner_calls += 1
            if self.planner_calls == 1:
                return ChatResult(
                    content=json.dumps(
                        {
                            "plan": {
                                "steps": [
                                    {
                                        "action": "read_file",
                                        "file_path": "README.md",
                                        "description": "读取 README，验证 action/file_path 兼容。",
                                    }
                                ]
                            }
                        },
                        ensure_ascii=False,
                    ),
                    provider=self.provider,
                    model="planner",
                )
            return ChatResult(
                content=json.dumps({"steps": [{"tool_name": "shell", "arguments": {"command": "rm -rf /"}}]}),
                provider=self.provider,
                model="planner",
            )
        self.chat_messages_seen.append(messages)
        has_runtime_context = any("[运行链上下文摘要]" in str(message.get("content", "")) for message in messages)
        return ChatResult(
            content="context=present" if has_runtime_context else "context=missing",
            provider=self.provider,
            model="chat",
        )


def test_l6_31_model_suggest_accepts_nested_plan_actions_and_direct_arguments() -> None:
    plan = validate_and_build_plan(
        {
            "plan": {
                "steps": [
                    {"action": "read_file", "file_path": "README.md", "description": "读取说明"},
                    {"name": "compileall", "target": "."},
                    {"tool": {"name": "create_zip_package"}, "parameters": {"source": ".", "output_path": "dist/demo.zip"}},
                ]
            }
        }
    )
    assert [step.tool_name for step in plan] == ["read_file", "run_python_quality_check", "create_zip_package"]
    assert plan[0].arguments == {"path": "README.md"}
    assert plan[1].arguments == {"command": "compileall", "target": "."}
    assert plan[2].arguments == {"source": ".", "target": "dist/demo.zip"}



def test_l6_31_model_suggest_accepts_schema_prompt_output_wrapper() -> None:
    plan = validate_and_build_plan(
        {
            "output": {
                "steps": [
                    {
                        "tool_name": "read_file",
                        "arguments": {"path": "README.md"},
                        "reason": "schema prompt top-level output wrapper",
                    }
                ]
            }
        }
    )
    assert len(plan) == 1
    assert plan[0].tool_name == "read_file"
    assert plan[0].arguments == {"path": "README.md"}

def test_l6_31_model_suggest_accepts_tool_calls_with_json_string_arguments() -> None:
    plan = validate_and_build_plan(
        {
            "tool_calls": [
                {"name": "read_file", "arguments": '{"path":"README.md"}'},
                {"name": "run_python_quality_check", "arguments": '{"command":"pytest", "target":"tests"}'},
            ]
        }
    )
    assert [step.tool_name for step in plan] == ["read_file", "run_python_quality_check"]
    assert plan[0].arguments["path"] == "README.md"
    assert plan[1].arguments == {"command": "pytest", "target": "tests"}


def test_l6_31_model_suggest_still_rejects_dangerous_unknown_payload() -> None:
    with pytest.raises(PlanValidationError) as exc_info:
        validate_and_build_plan({"steps": [{"action": "read_file", "arguments": {"path": "README.md", "cmd": "rm -rf /"}}]})
    assert {issue.code for issue in exc_info.value.issues} == {"unsafe_unknown_arguments"}


def test_l6_31_runtime_records_execution_summary_before_model_suggest_chat_fallback(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    client = ShapeThenFailClient()
    config = ModelConfig(
        provider="mock",
        model="mock-model",
        tool_execution_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        planner_mode=PlannerMode.MODEL_SUGGEST,
    )
    context = build_agent_context(config, workspace=tmp_path, max_steps=5)
    context.model_client = client

    first_code = run_runtime_task(context, "请读取 README")
    assert first_code == 0
    assert any("[运行链上下文摘要]" in message["content"] for message in context.session.messages if message["role"] == "assistant")

    second_code = run_runtime_task(context, "上面代码继续说明一下")
    assert second_code == 0
    assert context.session.messages[-1]["content"] == "context=present"
    assert client.chat_messages_seen
    assert any("[运行链上下文摘要]" in message["content"] for message in client.chat_messages_seen[-1])


def test_l6_31_deepseek_plan_shape_accepts_single_step_object() -> None:
    plan = validate_and_build_plan({"action": "read_file", "file_path": "README.md", "description": "DeepSeek single-step object"})
    assert len(plan) == 1
    assert plan[0].tool_name == "read_file"
    assert plan[0].arguments == {"path": "README.md"}


def test_l6_31_deepseek_plan_shape_accepts_stringified_nested_plan() -> None:
    plan = validate_and_build_plan({"plan": '{"steps":[{"action":"read_file","file_path":"README.md"}]}'})
    assert len(plan) == 1
    assert plan[0].tool_name == "read_file"
    assert plan[0].arguments == {"path": "README.md"}


def test_l6_31_deepseek_plan_shape_accepts_function_call_tool_shape() -> None:
    plan = validate_and_build_plan(
        {
            "tool_calls": [
                {
                    "function": {
                        "name": "read_file",
                        "arguments": '{"path":"README.md"}',
                    }
                }
            ]
        }
    )
    assert len(plan) == 1
    assert plan[0].tool_name == "read_file"
    assert plan[0].arguments == {"path": "README.md"}


def test_l6_31_deepseek_plan_shape_accepts_chinese_keys() -> None:
    plan = validate_and_build_plan({"计划": [{"工具名称": "read_file", "参数": {"路径": "README.md"}}]})
    assert len(plan) == 1
    assert plan[0].tool_name == "read_file"
    assert plan[0].arguments == {"path": "README.md"}


def test_l6_31_deepseek_plan_shape_accepts_execution_steps_and_command_alias() -> None:
    plan = validate_and_build_plan({"execution_steps": [{"operation": "质量检查", "检查命令": "compileall", "target": "."}]})
    assert len(plan) == 1
    assert plan[0].tool_name == "run_python_quality_check"
    assert plan[0].arguments == {"target": ".", "command": "compileall"}


def test_l6_31_deepseek_plan_shape_accepts_tool_object_with_input_params() -> None:
    plan = validate_and_build_plan(
        {"tasks": [{"tool": {"name": "create_zip_package"}, "input_params": {"source": ".", "目标路径": "dist/deepseek.zip"}}]}
    )
    assert len(plan) == 1
    assert plan[0].tool_name == "create_zip_package"
    assert plan[0].arguments == {"source": ".", "target": "dist/deepseek.zip"}


def test_l6_31_deepseek_plan_shape_compatibility_keeps_a5_and_shell_blocked() -> None:
    with pytest.raises(PlanValidationError) as exc_info:
        validate_and_build_plan({"tool_calls": [{"function": {"name": "shell", "arguments": '{"cmd":"rm -rf /"}'}}]})
    codes = {issue.code for issue in exc_info.value.issues}
    assert "tool_not_allowed" in codes
