"""L6.72.13 Organ emit_card wiring smoke tests.

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
os.environ.setdefault("TIANGONG_SOUL_BASELINE_PATH", str(Path(tempfile.gettempdir()) / "linyuanzhe_l67213_organ_emit_soul_emotion_baseline.json"))
os.environ.setdefault("TIANGONG_PROMPT_TRACE_FILE", str(Path(tempfile.gettempdir()) / "linyuanzhe_l67213_organ_emit_prompt_trace.jsonl"))
os.environ.setdefault("TIANGONG_PROMPT_TUNER_FILE", str(Path(tempfile.gettempdir()) / "linyuanzhe_l67213_organ_emit_prompt_tuning_state.json"))

from tiangong_agent_runtime.planner_mode import PlannerMode
from tiangong_agent_shell.cli_loop import run_once
from tiangong_agent_shell.composition_root import build_agent_context
from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.model_client_port import ChatResult, ensure_compiled_prompt_envelope
from tiangong_agent_shell.organ_signal_emitters import collect_organ_signal_cards, refresh_session_system_prompt
from tiangong_agent_shell.prompt_compiler import compile_prompt, build_desktop_context
from tiangong_agent_shell.tool_bridge import ToolExecutionMode


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

    def __init__(self, responder: Callable[[list[dict[str, str]], ModelConfig], str] | None = None) -> None:
        self.calls: list[list[dict[str, str]]] = []
        self.responder = responder or (lambda _messages, _config: "OK")

    def chat(self, prompt, config: ModelConfig) -> ChatResult:
        envelope = ensure_compiled_prompt_envelope(prompt)
        messages = envelope.as_messages()
        self.calls.append([dict(item) for item in messages])
        if envelope.phase == "activation_decision":
            return ChatResult(
                content=(
                    '{"mode":"chat","work_type":"none","execution_depth":"single_turn",'
                    '"tools_requested":false,"risk_level":"A0","need_quality_gate":false,'
                    '"need_user_confirm":false,"reason":"普通聊天。"}'
                ),
                provider=self.provider,
                model=config.model,
            )
        return ChatResult(content=self.responder(messages, config), provider=self.provider, model=config.model)


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


def test_collects_standard_organ_cards_without_prompt_sprawl() -> None:
    context = build_agent_context(_ready_config(), workspace=Path.cwd())
    cards = collect_organ_signal_cards(context, user_text="普通聊天", task_mode="ordinary_chat")
    types = {card.organ_type for card in cards}
    assert {"ui", "provider", "runtime", "tool", "risk", "planner"}.issubset(types)
    assert all(card.prompt_fragment is False for card in cards)
    assert all(card.direct_execution is False for card in cards)
    provider = [card for card in cards if card.organ_type == "provider"][0]
    assert provider.summary != "[redacted-sensitive-summary]"
    assert "key_ready" in provider.summary
    assert "api_key" not in provider.summary.lower()


def test_refresh_session_system_prompt_injects_selected_cards_and_preserves_history() -> None:
    with EnvPatch(TIANGONG_ENTRY_CHANNEL="desktop_gui"):
        context = build_agent_context(_ready_config(), workspace=Path.cwd())
        context.session.add_user("历史用户消息")
        context.session.add_assistant("历史助手消息")
        old_dialog = [m for m in context.session.messages if m.get("role") != "system"]
        cards = refresh_session_system_prompt(context, user_text="继续", task_mode="ordinary_chat")
        assert cards
        new_dialog = [m for m in context.session.messages if m.get("role") != "system"]
        assert new_dialog == old_dialog
        system = context.session.messages[0]["content"]
    assert "[OrganSignalCards / 器官信号卡]" in system
    assert "UIStateCard" in system
    assert "RuntimeCard" in system or "RiskCard" in system
    # PlannerCard may be collected, but ordinary_chat AttentionGate must not inject it.
    assert "PlannerCard(planner)" not in system
    assert "天工造物 v2.0 - 临渊者桌面端" in system


def test_run_once_refreshes_prompt_before_model_call() -> None:
    with EnvPatch(TIANGONG_ENTRY_CHANNEL="desktop_gui", TIANGONG_TASK_MODE="ordinary_chat"):
        context = build_agent_context(_ready_config(planner_mode=PlannerMode.MODEL_SUGGEST), workspace=Path.cwd())

        def responder(messages: list[dict[str, str]], _config: ModelConfig) -> str:
            system = messages[0]["content"]
            assert "[OrganSignalCards / 器官信号卡]" in system
            assert "PlannerCard(planner)" not in system
            assert "最小 CLI 模式" not in system
            return "器官卡链路OK"

        fake = FakeModelClient(responder)
        context.model_client = fake
        code, out, err = _run_capture(context, "你好，普通聊天")
    assert code == 0, err
    assert fake.calls
    assert "器官卡链路OK" in out
    assert "[计划器]" not in out


def test_code_task_can_inject_tool_runtime_cards() -> None:
    context = build_agent_context(_ready_config(planner_mode=PlannerMode.MODEL_SUGGEST), workspace=Path.cwd())
    cards = collect_organ_signal_cards(context, user_text="修复代码", task_mode="code_task")
    bundle = compile_prompt(build_desktop_context(_ready_config(), task_mode="code_task", organ_signal_cards=cards))
    prompt = bundle.system_prompt
    assert "ToolCard" in prompt or "RuntimeCard" in prompt
    assert "工具模式" in prompt
    assert "PlannerCard(planner)" in prompt or "Planner 是小脑建议器" in prompt


def test_static_no_core_pollution() -> None:
    project_root = Path(__file__).resolve().parent
    source = (project_root / "tiangong_agent_shell/organ_signal_emitters.py").read_text(encoding="utf-8")
    assert "tiangong_kernel" not in source
    assert "subprocess" not in source
    assert "while True" not in source
    assert "run_text(" not in source
    assert "execute_plan(" not in source
    assert "import v1" not in source.lower()


def main() -> int:
    tests = [
        test_collects_standard_organ_cards_without_prompt_sprawl,
        test_refresh_session_system_prompt_injects_selected_cards_and_preserves_history,
        test_run_once_refreshes_prompt_before_model_call,
        test_code_task_can_inject_tool_runtime_cards,
        test_static_no_core_pollution,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("L6.72.13 Organ emit_card wiring smoke PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
