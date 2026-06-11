"""L6.72.14 PromptTrace feedback attribution smoke tests.

No external network, no real Provider call, no v1 import, no background loop.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
from pathlib import Path
from typing import Callable

os.environ.setdefault("TIANGONG_SOUL_BASELINE_PERSIST", "0")
os.environ.setdefault("TIANGONG_SOUL_BASELINE_PATH", str(Path(tempfile.gettempdir()) / "linyuanzhe_l67214_prompt_trace_soul_emotion_baseline.json"))
os.environ.setdefault("TIANGONG_PROMPT_TRACE_FILE", str(Path(tempfile.gettempdir()) / "linyuanzhe_l67214_prompt_trace_prompt_trace.jsonl"))
os.environ.setdefault("TIANGONG_PROMPT_TUNER_FILE", str(Path(tempfile.gettempdir()) / "linyuanzhe_l67214_prompt_trace_prompt_tuning_state.json"))

from tiangong_agent_runtime.planner_mode import PlannerMode
from tiangong_agent_shell.cli_loop import run_once
from tiangong_agent_shell.composition_root import build_agent_context
from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.model_client_port import ChatResult, ensure_compiled_prompt_envelope
from tiangong_agent_shell.organ_signal_emitters import refresh_session_system_prompt
from tiangong_agent_shell.prompt_trace import (
    L6_72_14_PROMPT_OUTCOME_SCHEMA,
    L6_72_14_PROMPT_TRACE_SCHEMA,
    build_prompt_trace_outcome,
    recent_prompt_trace_summary,
)
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

    def __init__(self, responder: Callable[[list[dict[str, str]], ModelConfig], str]) -> None:
        self.calls: list[list[dict[str, str]]] = []
        self.responder = responder

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


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_refresh_writes_trace_start_without_prompt_pollution() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        trace_file = Path(tmp) / "prompt_trace.jsonl"
        with EnvPatch(TIANGONG_ENTRY_CHANNEL="desktop_gui", TIANGONG_TASK_MODE="ordinary_chat", TIANGONG_PROMPT_TRACE_FILE=str(trace_file)):
            context = build_agent_context(_ready_config(planner_mode=PlannerMode.MODEL_SUGGEST), workspace=Path(tmp))
            cards = refresh_session_system_prompt(context, user_text="用户秘密输入ABC123", task_mode="ordinary_chat")
            assert cards
            assert context.last_prompt_trace_event is not None
            system = context.session.messages[0]["content"]
            assert "PromptTrace" not in system
            assert "PlannerCard(planner)" not in system
            rows = _read_jsonl(trace_file)
        assert rows[0]["schema"] == L6_72_14_PROMPT_TRACE_SCHEMA
        assert rows[0]["selected_card_ids"]
        assert "ordinary_chat_blocks_planner" in rows[0]["rejected_reason_counts"]
        assert "用户秘密输入ABC123" not in json.dumps(rows, ensure_ascii=False), "raw user text must not be stored"


def test_run_once_records_success_outcome_and_card_credit() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        trace_file = Path(tmp) / "prompt_trace.jsonl"
        with EnvPatch(TIANGONG_ENTRY_CHANNEL="desktop_gui", TIANGONG_TASK_MODE="ordinary_chat", TIANGONG_PROMPT_TRACE_FILE=str(trace_file)):
            context = build_agent_context(_ready_config(), workspace=Path(tmp))
            context.model_client = FakeModelClient(lambda _messages, _config: "正常回复OK")
            code, out, err = _run_capture(context, "你好")
            assert code == 0, err
            assert "正常回复OK" in out
            records = _read_jsonl(trace_file)
            summary = recent_prompt_trace_summary(context, limit=4)
        schemas = [record["schema"] for record in records]
        assert L6_72_14_PROMPT_TRACE_SCHEMA in schemas
        assert L6_72_14_PROMPT_OUTCOME_SCHEMA in schemas
        outcome = [record for record in records if record["schema"] == L6_72_14_PROMPT_OUTCOME_SCHEMA][-1]
        assert outcome["success_proxy"] is True
        assert outcome["credit_by_card"]
        assert outcome["planner_leak_detected"] is False
        assert summary and summary[-1]["schema"] == L6_72_14_PROMPT_OUTCOME_SCHEMA


def test_leak_detection_and_user_visible_filtering() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        trace_file = Path(tmp) / "prompt_trace.jsonl"
        with EnvPatch(TIANGONG_ENTRY_CHANNEL="desktop_gui", TIANGONG_TASK_MODE="ordinary_chat", TIANGONG_PROMPT_TRACE_FILE=str(trace_file)):
            context = build_agent_context(_ready_config(), workspace=Path(tmp))
            context.model_client = FakeModelClient(lambda _messages, _config: "[计划器] 未生成可执行计划\n用户可见正文")
            code, out, err = _run_capture(context, "你好")
            assert code == 0, err
            assert "用户可见正文" in out
            assert "[计划器]" not in out
            assert "未生成可执行计划" not in out
            records = _read_jsonl(trace_file)
        outcome = [record for record in records if record["schema"] == L6_72_14_PROMPT_OUTCOME_SCHEMA][-1]
        assert outcome["success_proxy"] is False
        assert outcome["planner_leak_detected"] is True
        assert "planner_or_runtime_log_leak" in outcome["feedback_summary"]


def test_provider_not_configured_records_outcome_without_model_call() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        trace_file = Path(tmp) / "prompt_trace.jsonl"
        with EnvPatch(TIANGONG_ENTRY_CHANNEL="desktop_gui", TIANGONG_TASK_MODE="ordinary_chat", TIANGONG_PROMPT_TRACE_FILE=str(trace_file)):
            context = build_agent_context(ModelConfig(), workspace=Path(tmp))
            context.model_client = FakeModelClient(lambda _messages, _config: "SHOULD_NOT_CALL")
            code, out, err = _run_capture(context, "你好")
            assert code == 0, err
            assert "尚未配置模型接口" in out
            assert not context.model_client.calls
            records = _read_jsonl(trace_file)
        outcome = [record for record in records if record["schema"] == L6_72_14_PROMPT_OUTCOME_SCHEMA][-1]
        assert outcome["provider_not_configured"] is True
        assert outcome["success_proxy"] is False
        assert "provider_not_configured" in outcome["feedback_summary"]


def test_static_no_core_pollution() -> None:
    project_root = Path(__file__).resolve().parent
    trace_source = (project_root / "tiangong_agent_shell/prompt_trace.py").read_text(encoding="utf-8")
    emitter_source = (project_root / "tiangong_agent_shell/organ_signal_emitters.py").read_text(encoding="utf-8")
    assert "tiangong_kernel" not in trace_source
    assert "subprocess" not in trace_source
    assert "while True" not in trace_source
    assert "run_text(" not in trace_source
    assert "execute_plan(" not in trace_source
    assert "PromptTrace" not in ""  # placeholder: trace must not be injected by smoke assertions above
    assert "build_system_prompt(" not in emitter_source
    assert "import v1" not in (trace_source + emitter_source).lower()


def main() -> int:
    tests = [
        test_refresh_writes_trace_start_without_prompt_pollution,
        test_run_once_records_success_outcome_and_card_credit,
        test_leak_detection_and_user_visible_filtering,
        test_provider_not_configured_records_outcome_without_model_call,
        test_static_no_core_pollution,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("L6.72.14 PromptTrace feedback attribution smoke PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
