"""L6.72.11 PromptCompiler smoke tests.

No external network, no real Provider call, no v1 import, no background loop.
"""

from __future__ import annotations

import contextlib
import io
import os
import tempfile
from pathlib import Path
from typing import Callable

os.environ.setdefault("TIANGONG_SOUL_BASELINE_PERSIST", "0")
os.environ.setdefault("TIANGONG_SOUL_BASELINE_PATH", str(Path(tempfile.gettempdir()) / "linyuanzhe_l67211_prompt_compiler_soul_emotion_baseline.json"))
os.environ.setdefault("TIANGONG_PROMPT_TRACE_FILE", str(Path(tempfile.gettempdir()) / "linyuanzhe_l67211_prompt_compiler_prompt_trace.jsonl"))
os.environ.setdefault("TIANGONG_PROMPT_TUNER_FILE", str(Path(tempfile.gettempdir()) / "linyuanzhe_l67211_prompt_compiler_prompt_tuning_state.json"))

from tiangong_agent_runtime.planner_mode import PlannerMode
from tiangong_agent_shell.composition_root import build_agent_context
from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.model_client_port import ChatResult, ensure_compiled_prompt_envelope
from tiangong_agent_shell.prompt_compiler import build_cli_context, build_desktop_context, compile_prompt
from tiangong_agent_shell.tool_bridge import ToolExecutionMode
from tiangong_agent_shell.cli_loop import run_once


class EnvPatch:
    def __init__(self, **values: str) -> None:
        self.values = values
        self.old: dict[str, str | None] = {}

    def __enter__(self) -> None:
        for key, value in self.values.items():
            self.old[key] = os.environ.get(key)
            os.environ[key] = value

    def __exit__(self, *_exc: object) -> None:
        for key, value in self.old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class FakeModelClient:
    provider = "fake_provider"

    def __init__(self, responder: Callable[..., str] | None = None) -> None:
        self.calls: list[list[dict[str, str]]] = []
        self.envelopes: list[object] = []
        self.responder = responder or (lambda _messages, _config: "普通聊天OK")

    def chat(self, prompt: object, config: ModelConfig) -> ChatResult:
        envelope = ensure_compiled_prompt_envelope(prompt)
        messages = envelope.as_messages()
        self.envelopes.append(envelope)
        self.calls.append([dict(item) for item in messages])
        if envelope.phase == "activation_decision":
            content = '{"mode":"chat","work_type":"none","execution_depth":"single_turn","tools_requested":false,"required_tool_classes":[],"risk_level":"A0","need_quality_gate":false,"need_user_confirm":false,"expected_result":"普通聊天","final_output_contract":"answer_only"}'
        elif envelope.phase in {"planner_plan", "planner_execution"}:
            content = '{"steps":[{"tool_name":"list_dir","arguments":{"path":"."},"reason":"smoke"}]}'
        else:
            try:
                content = self.responder(messages, config, envelope)
            except TypeError:
                content = self.responder(messages, config)
        return ChatResult(content=content, provider=self.provider, model=config.model)


def _ready_config(*, planner_mode: PlannerMode = PlannerMode.RULE_ONLY) -> ModelConfig:
    return ModelConfig(
        provider="deepseek",
        base_url="https://example.invalid/v1",
        api_key="MOCK_PROVIDER_KEY_SHOULD_REDACT",
        model="deepseek-chat",
        tool_execution_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        planner_mode=planner_mode,
    )


def _run_capture(context, text: str) -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = run_once(context, text)
    return code, out.getvalue(), err.getvalue()


def test_desktop_prompt() -> None:
    with EnvPatch(TIANGONG_SOUL_NAME="临渊者A", TIANGONG_SOUL_PROMPT="稳定、直接、执行力第一。"):
        prompt = compile_prompt(build_desktop_context(_ready_config())).system_prompt
    assert "天工造物 v2.0 - 临渊者桌面端" in prompt
    assert "最小 CLI 模式" not in prompt
    assert "本体名称：临渊者A" in prompt


def test_cli_prompt() -> None:
    prompt = compile_prompt(build_cli_context(_ready_config())).system_prompt
    assert "CLI 入口" in prompt
    assert "临渊者桌面端" not in prompt


def test_soul_injection_changes() -> None:
    with EnvPatch(TIANGONG_SOUL_NAME="临渊者A"):
        a = compile_prompt(build_desktop_context(_ready_config())).system_prompt
    with EnvPatch(TIANGONG_SOUL_NAME="临渊者B"):
        b = compile_prompt(build_desktop_context(_ready_config())).system_prompt
    assert "临渊者A" in a
    assert "临渊者B" in b
    assert a != b


def test_tool_mode_cards() -> None:
    runtime_prompt = compile_prompt(build_desktop_context(_ready_config())).system_prompt
    disabled_cfg = ModelConfig(provider="deepseek", base_url="x", api_key="mockkey_real-1", model="m", tool_execution_mode=ToolExecutionMode.DISABLED)
    disabled_prompt = compile_prompt(build_desktop_context(disabled_cfg)).system_prompt
    assert "工具由 Runtime 管控" in runtime_prompt
    assert "当前工具禁用" in disabled_prompt


def test_ordinary_chat_no_planner_output() -> None:
    with EnvPatch(TIANGONG_TASK_MODE="ordinary_chat", TIANGONG_ENTRY_CHANNEL="desktop_gui"):
        cfg = _ready_config(planner_mode=PlannerMode.MODEL_SUGGEST)
        context = build_agent_context(cfg, workspace=Path.cwd())
        context.model_client = FakeModelClient(lambda _messages, _config: "普通聊天OK")
        code, out, err = _run_capture(context, "你好，普通聊天")
    assert code == 0, err
    for forbidden in ("[运行链]", "【运行链】", "未生成可执行计划", "[计划器]", "【计划器】"):
        assert forbidden not in out
    assert "普通聊天OK" in out


def test_provider_not_configured_no_mock() -> None:
    with EnvPatch(TIANGONG_ENTRY_CHANNEL="desktop_gui", TIANGONG_TASK_MODE="ordinary_chat"):
        context = build_agent_context(ModelConfig(), workspace=Path.cwd())
        context.model_client = FakeModelClient(lambda _messages, _config: "MOCK SHOULD NOT RUN")
        code, out, err = _run_capture(context, "你好")
    assert code == 0, err
    assert "尚未配置模型接口" in out
    assert "MOCK SHOULD NOT RUN" not in out
    assert "mock" not in out.lower()


def test_provider_configured_real_chain_shape() -> None:
    with EnvPatch(TIANGONG_ENTRY_CHANNEL="desktop_gui", TIANGONG_TASK_MODE="ordinary_chat"):
        context = build_agent_context(_ready_config(), workspace=Path.cwd())
        fake = FakeModelClient(lambda _messages, _config: "真实链路形态OK")
        context.model_client = fake
        code, out, err = _run_capture(context, "短消息联调")
    assert code == 0, err
    assert fake.calls, "model client should be called"
    assert "真实链路形态OK" in out


def test_conversation_continuity_and_new_conversation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        conv = str(Path(tmp) / "conversation.json")
        with EnvPatch(TIANGONG_ENTRY_CHANNEL="desktop_gui", TIANGONG_TASK_MODE="ordinary_chat", TIANGONG_CONVERSATION_FILE=conv):
            c1 = build_agent_context(_ready_config(), workspace=Path.cwd())
            c1.model_client = FakeModelClient(lambda _messages, _config: "第一轮答复")
            code1, out1, err1 = _run_capture(c1, "第一轮")
            assert code1 == 0, err1
            assert "第一轮答复" in out1

            def responder(messages: list[dict[str, str]], _config: ModelConfig) -> str:
                joined = "\n".join(str(m.get("content", "")) for m in messages)
                return "看到上文" if "第一轮答复" in joined else "未看到上文"

            c2 = build_agent_context(_ready_config(), workspace=Path.cwd())
            c2.model_client = FakeModelClient(responder)
            code2, out2, err2 = _run_capture(c2, "第二轮")
            assert code2 == 0, err2
            assert "看到上文" in out2

        Path(conv).unlink(missing_ok=True)
        with EnvPatch(TIANGONG_ENTRY_CHANNEL="desktop_gui", TIANGONG_TASK_MODE="ordinary_chat", TIANGONG_CONVERSATION_FILE=conv):
            c3 = build_agent_context(_ready_config(), workspace=Path.cwd())
            c3.model_client = FakeModelClient(lambda messages, _config: "有旧上文" if any("第一轮答复" in m.get("content", "") for m in messages) else "新会话干净")
            code3, out3, err3 = _run_capture(c3, "新会话")
            assert code3 == 0, err3
            assert "新会话干净" in out3


def test_no_pollution_static() -> None:
    project_root = Path(__file__).resolve().parent
    builder = (project_root / "tiangong_agent_shell/prompt_builder.py").read_text(encoding="utf-8")
    compiler = (project_root / "tiangong_agent_shell/prompt_compiler.py").read_text(encoding="utf-8")
    assert "_desktop_prompt" not in builder
    assert "_cli_prompt" not in builder
    assert "最小 CLI 模式" not in compiler
    assert "import v1" not in compiler.lower()


def main() -> int:
    tests = [
        test_desktop_prompt,
        test_cli_prompt,
        test_soul_injection_changes,
        test_tool_mode_cards,
        test_ordinary_chat_no_planner_output,
        test_provider_not_configured_no_mock,
        test_provider_configured_real_chain_shape,
        test_conversation_continuity_and_new_conversation,
        test_no_pollution_static,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("L6.72.11 PromptCompiler smoke PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
