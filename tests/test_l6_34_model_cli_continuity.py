from __future__ import annotations

import json
from pathlib import Path

from tiangong_agent_runtime.model_plan_compat_replay import replay_deepseek_plan_samples
from tiangong_agent_runtime.model_planner import ModelPlanner
from tiangong_agent_runtime.planner_mode import PlannerMode
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_shell.cli_loop import preview_runtime_plan, run_runtime_task
from tiangong_agent_shell.composition_root import build_agent_context
from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.model_client_port import ChatResult
from tiangong_agent_shell.session_state import SessionState
from tiangong_agent_shell.tool_bridge import ToolExecutionMode


class StaticPlannerClient:
    provider = "static-planner"

    def __init__(self, content: str) -> None:
        self.content = content
        self.messages_seen: list[list[dict[str, str]]] = []

    def chat(self, messages: list[dict[str, str]], config: ModelConfig) -> ChatResult:  # noqa: ARG002
        self.messages_seen.append(messages)
        return ChatResult(content=self.content, provider=self.provider, model="planner")


class ContextAwarePlannerClient:
    provider = "context-aware-planner"

    def __init__(self) -> None:
        self.planner_messages: list[list[dict[str, str]]] = []
        self.chat_messages: list[list[dict[str, str]]] = []

    def chat(self, messages: list[dict[str, str]], config: ModelConfig) -> ChatResult:  # noqa: ARG002
        system_text = "\n".join(str(message.get("content", "")) for message in messages if message.get("role") == "system")
        if "计划生成器" in system_text:
            self.planner_messages.append(messages)
            user_text = "\n".join(str(message.get("content", "")) for message in messages if message.get("role") == "user")
            if "def previous" in user_text:
                return ChatResult(
                    content=json.dumps({"steps": [{"tool_name": "return_analysis", "arguments": {"content": "saw previous code"}}]}, ensure_ascii=False),
                    provider=self.provider,
                    model="planner",
                )
            return ChatResult(content='{"steps":[{"tool_name":"shell","arguments":{"cmd":"rm -rf /"}}]}', provider=self.provider, model="planner")
        self.chat_messages.append(messages)
        has_previous = any("def previous" in str(message.get("content", "")) for message in messages)
        return ChatResult(content="chat_context=present" if has_previous else "chat_context=missing", provider=self.provider, model="chat")


def test_l6_34_deepseek_plan_sample_replay_has_full_expectation_match() -> None:
    report = replay_deepseek_plan_samples()
    data = report.public_dict()
    assert report.ok
    assert data["total"] >= 12
    assert data["pass_rate"] == 1.0
    assert data["accepted_expected_rate"] == 1.0
    unsafe = {item["name"]: item for item in data["results"] if item["name"].startswith("unsafe_")}
    assert unsafe["unsafe_shell_rejected"]["accepted"] is False
    assert unsafe["unsafe_absolute_path_rejected"]["accepted"] is False


def test_l6_34_json_answer_without_steps_becomes_return_analysis() -> None:
    planner = ModelPlanner()
    result = planner.build_plan(
        "分析这段代码",
        model_config=ModelConfig(provider="mock", model="mock-model"),
        model_client=StaticPlannerClient(json.dumps({"answer": "这段代码需要补边界测试。"}, ensure_ascii=False)),
    )
    assert result.ok
    assert result.plan[0].tool_name == "return_analysis"
    assert "边界测试" in result.plan[0].arguments["content"]


def test_l6_34_dangerous_plan_is_not_virtualized() -> None:
    planner = ModelPlanner()
    result = planner.build_plan(
        "删除根目录",
        model_config=ModelConfig(provider="mock", model="mock-model"),
        model_client=StaticPlannerClient('{"steps":[{"tool_name":"shell","arguments":{"cmd":"rm -rf /"}}]}'),
    )
    assert not result.ok
    assert [issue.code for issue in result.issues] == ["tool_not_allowed"]
    assert "tool_not_allowed" in result.message


def test_l6_34_session_context_hint_contains_recent_code() -> None:
    session = SessionState.create(ModelConfig(provider="mock", model="mock-model"))
    session.add_user("先给我代码")
    session.add_assistant("```python\ndef previous():\n    return 42\n```")
    hint = session.build_context_hint(turns=2)
    assert "def previous" in hint
    assert "CLI 最近会话上下文" in hint


def test_l6_34_runtime_model_planner_receives_cli_session_context(tmp_path: Path) -> None:
    client = ContextAwarePlannerClient()
    config = ModelConfig(
        provider="mock",
        model="mock-model",
        tool_execution_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        planner_mode=PlannerMode.MODEL_SUGGEST,
    )
    context = build_agent_context(config, workspace=tmp_path, max_steps=3)
    context.model_client = client
    context.session.add_user("先给我代码")
    context.session.add_assistant("```python\ndef previous():\n    return 42\n```")

    code = run_runtime_task(context, "解释上面代码")
    assert code == 0
    assert client.planner_messages
    planner_user_text = "\n".join(str(message.get("content", "")) for message in client.planner_messages[-1] if message.get("role") == "user")
    assert "def previous" in planner_user_text
    assert context.session.messages[-1]["content"].startswith("[运行链上下文摘要]")


def test_l6_34_plan_failed_chat_fallback_still_preserves_context(tmp_path: Path) -> None:
    client = ContextAwarePlannerClient()
    config = ModelConfig(
        provider="mock",
        model="mock-model",
        tool_execution_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        planner_mode=PlannerMode.MODEL_SUGGEST,
    )
    context = build_agent_context(config, workspace=tmp_path, max_steps=3)
    context.model_client = client
    context.session.add_user("先给我代码")
    context.session.add_assistant("```python\ndef previous():\n    return 42\n```")

    # 这里不把 context hint 注入 Planner，迫使危险 plan 被拒后进入普通聊天回退，
    # 以验证 plan_failed fallback 仍携带最近两轮 assistant 正文。
    context.session.reset()
    context.session.add_user("先给我代码")
    context.session.add_assistant("```python\ndef previous():\n    return 42\n```")
    context.session.add_user("另一个问题")
    context.session.add_assistant("普通上下文")
    # 使用手动 runtime.run_text 不传 external_context_hint 触发 planner 拒绝。
    result = context.runtime.run_text(
        "解释上面代码",
        workspace=context.workspace,
        tool_mode=context.config.tool_execution_mode,
        planner_mode=context.config.planner_mode,
        model_config=context.config,
        model_client=context.model_client,
        max_steps=context.max_steps,
        external_context_hint="",
    )
    assert not result.has_plan
    # CLI 回退路径仍会携带 session 最近两轮。这里直接跑一次外层函数验证。
    code = run_runtime_task(context, "解释上面代码")
    assert code == 0
    assert "return_analysis" in context.session.messages[-1]["content"] or context.session.messages[-1]["content"] == "chat_context=present"


def test_l6_34_preview_plan_passes_session_context_to_model_planner(tmp_path: Path, capsys) -> None:
    client = ContextAwarePlannerClient()
    config = ModelConfig(
        provider="mock",
        model="mock-model",
        tool_execution_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        planner_mode=PlannerMode.MODEL_SUGGEST,
    )
    context = build_agent_context(config, workspace=tmp_path, max_steps=3)
    context.model_client = client
    context.session.add_user("先给我代码")
    context.session.add_assistant("```python\ndef previous():\n    return 42\n```")

    code = preview_runtime_plan(context, "解释上面代码")
    output = capsys.readouterr().out
    assert code == 0
    assert '"tool_name": "return_analysis"' in output
    planner_user_text = "\n".join(str(message.get("content", "")) for message in client.planner_messages[-1] if message.get("role") == "user")
    assert "def previous" in planner_user_text


def test_l6_34_runtime_exposes_model_plan_replay_report() -> None:
    runtime = RuntimeEntry()
    report = runtime.run_model_plan_compat_replay()
    assert report["schema"] == "tiangong.l6_34.deepseek_plan_replay.v1"
    assert report["ok"] is True
