from __future__ import annotations

from pathlib import Path

from tiangong_agent_runtime.model_planner import ModelPlanner
from tiangong_agent_runtime.plan_schema import validate_and_build_plan
from tiangong_agent_runtime.planner_mode import PlannerMode
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.tool_result import ToolResultStatus
from tiangong_agent_shell.cli_loop import _messages_for_plan_failed_fallback, run_runtime_task
from tiangong_agent_shell.composition_root import build_agent_context
from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.model_client_port import ChatResult
from tiangong_agent_shell.tool_bridge import ToolExecutionMode


class PlainCodeClient:
    provider = "plain-code"

    def __init__(self) -> None:
        self.messages_seen: list[list[dict[str, str]]] = []

    def chat(self, messages: list[dict[str, str]], config: ModelConfig) -> ChatResult:  # noqa: ARG002
        self.messages_seen.append(messages)
        return ChatResult(
            content="```python\ndef add(a, b):\n    return a + b\n```",
            provider=self.provider,
            model="planner",
        )


class InvalidPlannerThenChatClient:
    provider = "invalid-then-chat"

    def __init__(self) -> None:
        self.chat_messages_seen: list[list[dict[str, str]]] = []

    def chat(self, messages: list[dict[str, str]], config: ModelConfig) -> ChatResult:  # noqa: ARG002
        system_text = "\n".join(str(message.get("content", "")) for message in messages if message.get("role") == "system")
        if "计划生成器" in system_text and "steps" in system_text:
            return ChatResult(
                content='{"steps":[{"tool_name":"shell","arguments":{"command":"rm -rf /"}}]}',
                provider=self.provider,
                model="planner",
            )
        self.chat_messages_seen.append(messages)
        has_previous_code = any("def important" in str(message.get("content", "")) for message in messages)
        return ChatResult(
            content="previous_code=present" if has_previous_code else "previous_code=missing",
            provider=self.provider,
            model="chat",
        )


def test_l6_32_p1_plain_code_model_output_becomes_return_code_plan() -> None:
    client = PlainCodeClient()
    planner = ModelPlanner()
    result = planner.build_plan(
        "写一个 add 函数",
        model_config=ModelConfig(provider="mock", model="mock-model"),
        model_client=client,
    )
    assert result.ok
    assert [step.tool_name for step in result.plan] == ["return_code"]
    assert result.plan[0].arguments["language"] == "python"
    assert "def add" in result.plan[0].arguments["content"]
    planner_prompt = "\n".join(message["content"] for message in client.messages_seen[0] if message["role"] == "system")
    assert "return_code" in planner_prompt
    assert "return_analysis" in planner_prompt



def test_l6_32_p1_json_code_payload_without_tool_name_becomes_return_code() -> None:
    plan = validate_and_build_plan({"steps": [{"code": "def f():\n    return 1", "language": "python"}]})
    assert len(plan) == 1
    assert plan[0].tool_name == "return_code"
    assert "def f" in plan[0].arguments["content"]


def test_l6_32_p1_plain_code_runtime_goes_through_audit_only_virtual_tool(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    result = runtime.run_text(
        "写一个 add 函数",
        workspace=tmp_path,
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        planner_mode=PlannerMode.MODEL_SUGGEST,
        model_config=ModelConfig(provider="mock", model="mock-model"),
        model_client=PlainCodeClient(),
        max_steps=3,
    )
    assert result.has_plan
    assert result.results[0].status is ToolResultStatus.OK
    assert result.results[0].tool_name == "return_code"
    assert result.results[0].data["audit_only"] is True
    assert result.results[0].data["executes_code"] is False
    assert not list(tmp_path.iterdir())


def test_l6_32_p1_plan_failed_fallback_carries_recent_assistant_code(tmp_path: Path) -> None:
    client = InvalidPlannerThenChatClient()
    config = ModelConfig(
        provider="mock",
        model="mock-model",
        tool_execution_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        planner_mode=PlannerMode.MODEL_SUGGEST,
    )
    context = build_agent_context(config, workspace=tmp_path, max_steps=3)
    context.model_client = client
    context.session.add_user("先给我代码")
    context.session.add_assistant("```python\ndef important():\n    return 42\n```")

    code = run_runtime_task(context, "解释上面代码")
    assert code == 0
    assert context.session.messages[-1]["content"] == "previous_code=present"
    assert client.chat_messages_seen
    assert any("def important" in str(message.get("content", "")) for message in client.chat_messages_seen[-1])
    direct_messages = _messages_for_plan_failed_fallback(context, "继续")
    assert any("def important" in str(message.get("content", "")) for message in direct_messages)


def test_l6_32_p1_blocked_step_does_not_consume_failure_budget(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    result = runtime.execute_plan(
        [
            ToolInvocation("read_file", {"path": ".env"}),
            ToolInvocation("read_file", {"path": "README.md"}),
        ],
        workspace=tmp_path,
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps=3,
    )
    assert result.results[0].status is ToolResultStatus.BLOCKED
    assert result.chain_summary is not None
    assert result.chain_summary.failure_count == 0
    assert result.chain_summary.stopped_reason == "blocked"


def test_l6_32_p2_plan_schema_allows_safe_prefix_tools_but_runtime_still_requires_registry(tmp_path: Path) -> None:
    plan = validate_and_build_plan({"steps": [{"tool_name": "read_custom_doc", "arguments": {"path": "README.md"}}]})
    assert plan[0].tool_name == "read_custom_doc"
    runtime = RuntimeEntry()
    result = runtime.execute_plan(plan, workspace=tmp_path, tool_mode=ToolExecutionMode.RUNTIME_GOVERNED, max_steps=1)
    assert result.results[0].status is ToolResultStatus.FAILED
    assert result.results[0].error_code == "tool_not_registered"


def test_l6_32_p2_workspace_write_capability_detects_unavailable_workspace(tmp_path: Path) -> None:
    missing = tmp_path / "missing_workspace"
    config = ModelConfig(provider="mock", model="mock-model", tool_execution_mode=ToolExecutionMode.RUNTIME_GOVERNED)
    context = build_agent_context(config, workspace=missing, max_steps=1)
    assert context.tool_bridge.capability_enabled("write_file") is False
    blocked = context.tool_bridge.execute("write_workspace_file", {"path": "x.txt", "content": "x"})
    assert blocked.allowed is False
    assert "写文件工具不可用" in blocked.message


def test_l6_32_p3_long_chain_progress_snapshots_are_exposed(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    plan = [ToolInvocation("list_dir", {"path": "."}) for _ in range(12)]
    result = runtime.execute_plan(plan, workspace=tmp_path, tool_mode=ToolExecutionMode.RUNTIME_GOVERNED, max_steps=20)
    assert all(item.status is ToolResultStatus.OK for item in result.results)
    assert result.chain_summary is not None
    assert len(result.chain_summary.progress_snapshots) >= 3
    report = runtime.planner_execution_snapshot()
    assert report["progress_snapshot_count"] >= 3
    assert "进度 5/12" in report["progress_snapshots"][0]["message"]
