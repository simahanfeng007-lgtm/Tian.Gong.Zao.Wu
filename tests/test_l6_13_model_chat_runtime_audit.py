from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.errors import ModelClientError
from tiangong_agent_shell.model_client_mock import MockModelClient
from tiangong_agent_shell.model_client_port import ChatResult
from tiangong_agent_shell.session_state import SessionState
from tiangong_agent_shell.tool_bridge import ToolExecutionMode


ROOT = Path(__file__).resolve().parents[1]


def test_model_chat_goes_through_runtime_audit_chain_without_prompt_or_key_leak(tmp_path: Path) -> None:
    config = ModelConfig(provider="mock", model="mock-model", api_key="sk-secret-123456")
    session = SessionState.create(config)
    session.add_user("请解释 rm 命令是什么，不要执行")
    runtime = RuntimeEntry()

    result = runtime.run_model_chat(
        session.messages,
        model_config=config,
        model_client=MockModelClient(),
        workspace=tmp_path,
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
    )

    assert result.results[0].ok
    assert result.results[0].tool_name == "model_chat"
    assert "[MOCK] 已收到" in result.results[0].data["content"]
    events = result.audit_events
    assert events[-1]["tool_name"] == "model_chat"
    assert events[-1]["risk_level"] == "A2"
    assert events[-1]["permit_status"] == "allowed"
    assert "messages" not in events[-1]["input_summary"]
    assert "sk-secret-123456" not in str(events)


def test_shell_mock_once_still_works_and_records_model_chat_label() -> None:
    proc = subprocess.run(
        [sys.executable, "run_agent.py", "--mock", "--once", "你好"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
    )
    assert proc.returncode == 0
    assert "[MOCK] 已收到：你好" in proc.stdout


class LeakyFailingClient:
    provider = "leaky"

    def chat(self, messages: list[dict[str, str]], config: ModelConfig) -> ChatResult:  # noqa: ARG002
        raise ModelClientError(
            "模型失败，key=sk-secret-abcdef",
            detail="detail contains sk-secret-abcdef",
        )


def test_model_client_error_is_redacted_in_runtime_result_and_audit(tmp_path: Path) -> None:
    config = ModelConfig(provider="openai_compatible", model="x", api_key="sk-secret-abcdef")
    session = SessionState.create(config)
    session.add_user("hello")
    runtime = RuntimeEntry()

    result = runtime.run_model_chat(
        session.messages,
        model_config=config,
        model_client=LeakyFailingClient(),
        workspace=tmp_path,
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
    )

    assert result.results[0].status.value == "failed"
    text = str(result.results[0].data) + result.results[0].output_summary + str(result.audit_events)
    assert "sk-secret-abcdef" not in text
    assert "<已配置:digest:" in text
