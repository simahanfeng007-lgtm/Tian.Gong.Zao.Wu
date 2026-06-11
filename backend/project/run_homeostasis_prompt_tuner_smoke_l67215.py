"""L6.72.15 HomeostasisPromptTuner smoke tests.

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
os.environ.setdefault("TIANGONG_SOUL_BASELINE_PATH", str(Path(tempfile.gettempdir()) / "linyuanzhe_l67215_soul_emotion_baseline.json"))

from tiangong_agent_runtime.planner_mode import PlannerMode
from tiangong_agent_shell.cli_loop import run_once
from tiangong_agent_shell.composition_root import build_agent_context
from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.homeostasis_prompt_tuner import (
    L6_72_15_PROMPT_TUNER_SCHEMA,
    baseline_prompt_tuning_state,
    prompt_tuning_public_summary,
    tune_prompt_state_from_outcome,
    tuned_min_score,
    tuned_score_bias,
)
from tiangong_agent_shell.model_client_port import ChatResult, ensure_compiled_prompt_envelope
from tiangong_agent_shell.organ_signal_card import emit_organ_signal_card, score_organ_signal_card, select_organ_signal_cards
from tiangong_agent_shell.organ_signal_emitters import refresh_session_system_prompt
from tiangong_agent_shell.prompt_compiler import build_desktop_context, compile_prompt, trace_prompt_organ_signals
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


def test_tuner_success_and_leak_update_are_bounded() -> None:
    base = baseline_prompt_tuning_state()
    success = tune_prompt_state_from_outcome(
        base,
        {
            "success_proxy": True,
            "model_ok": True,
            "credit_by_organ": {"memory": 1.0, "skill": 1.0},
            "feedback_summary": "success",
        },
    )
    assert success.sample_count == 1
    assert success.success_ema > base.success_ema
    assert success.public_dict()["organ_bias"]["memory"] > 0
    leak = tune_prompt_state_from_outcome(
        success,
        {
            "success_proxy": False,
            "model_ok": True,
            "planner_leak_detected": True,
            "internal_log_leak_detected": True,
            "credit_by_organ": {"planner": -1.0, "runtime": -0.4, "audit": -0.5},
            "feedback_summary": "planner_or_runtime_log_leak",
        },
    )
    data = leak.public_dict()
    assert data["schema"] == L6_72_15_PROMPT_TUNER_SCHEMA
    assert data["planner_leak_pressure"] > 0
    assert data["global_threshold_delta"] > 0
    assert data["organ_bias"]["planner"] < 0
    assert -0.35 <= data["organ_bias"]["planner"] <= 0.35


def test_attention_gate_uses_homeostasis_bias_without_overriding_hard_boundary() -> None:
    state = tune_prompt_state_from_outcome(
        baseline_prompt_tuning_state(),
        {
            "success_proxy": False,
            "model_ok": True,
            "planner_leak_detected": True,
            "credit_by_organ": {"planner": -1.0, "skill": 1.0},
        },
    ).public_dict()
    planner = emit_organ_signal_card(
        organ_type="planner",
        summary="普通聊天里不应进入 Planner。",
        source="planner_smoke",
        task_relevance=1.0,
        confidence=1.0,
        utility_history=1.0,
    )
    skill = emit_organ_signal_card(
        organ_type="skill",
        summary="代码任务中 compileall 和 smoke 是强执行经验。",
        source="skill_smoke",
        task_relevance=0.86,
        confidence=0.86,
        utility_history=0.86,
    )
    assert tuned_score_bias(planner, task_mode="ordinary_chat", tuning_state=state) < -1.0
    assert planner not in select_organ_signal_cards([planner, skill], task_mode="ordinary_chat", tuning_state=state)
    base_score = score_organ_signal_card(skill, task_mode="code_task").value
    tuned_score = score_organ_signal_card(skill, task_mode="code_task", tuning_state=state).value
    assert tuned_score != base_score
    assert tuned_min_score(task_mode="ordinary_chat", base_min_score=1.6, tuning_state=state) >= 1.6


def test_prompt_compiler_trace_contains_tuning_bias_and_no_prompt_pollution() -> None:
    state = tune_prompt_state_from_outcome(
        baseline_prompt_tuning_state(),
        {"success_proxy": True, "model_ok": True, "credit_by_organ": {"memory": 1.0}},
    ).public_dict()
    memory = emit_organ_signal_card(
        organ_type="memory",
        summary="用户偏好执行力第一、少废话。",
        source="memory_smoke",
        task_relevance=0.9,
        confidence=0.9,
        utility_history=0.9,
    )
    ctx = build_desktop_context(
        _ready_config(),
        task_mode="ordinary_chat",
        organ_signal_cards=[memory],
        prompt_tuning_state=state,
    )
    bundle = compile_prompt(ctx)
    trace = trace_prompt_organ_signals(ctx)
    assert "HomeostasisPromptTuner" not in bundle.system_prompt
    assert "PromptTrace" not in bundle.system_prompt
    assert any(row["score"].get("tuning_bias") != 0 for row in trace)


def test_run_once_updates_and_persists_tuner_state() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        trace_file = Path(tmp) / "prompt_trace.jsonl"
        tuner_file = Path(tmp) / "prompt_tuning_state.json"
        with EnvPatch(
            TIANGONG_ENTRY_CHANNEL="desktop_gui",
            TIANGONG_TASK_MODE="ordinary_chat",
            TIANGONG_PROMPT_TRACE_FILE=str(trace_file),
            TIANGONG_PROMPT_TUNER_FILE=str(tuner_file),
            TIANGONG_SOUL_BASELINE_PERSIST="0",
            TIANGONG_SOUL_BASELINE_PATH=str(Path(tmp) / "soul_emotion_baseline.json"),
        ):
            context = build_agent_context(_ready_config(), workspace=Path(tmp))
            context.model_client = FakeModelClient(lambda _messages, _config: "[计划器] 未生成可执行计划\n用户可见正文")
            code, out, err = _run_capture(context, "你好")
            assert code == 0, err
            assert "用户可见正文" in out
            assert "[计划器]" not in out
            assert tuner_file.exists()
            state = json.loads(tuner_file.read_text(encoding="utf-8"))
            assert state["schema"] == L6_72_15_PROMPT_TUNER_SCHEMA
            assert state["planner_leak_pressure"] > 0
            assert state["global_threshold_delta"] > 0
            refresh_session_system_prompt(context, user_text="第二轮", task_mode="ordinary_chat")
            summary = prompt_tuning_public_summary(context)
            assert summary["sample_count"] >= 1
            records = _read_jsonl(trace_file)
        assert any(record.get("schema") == "tiangong.l6_72_14.prompt_trace_outcome.v1" for record in records)


def test_static_no_core_pollution() -> None:
    project_root = Path(__file__).resolve().parent
    source = (project_root / "tiangong_agent_shell/homeostasis_prompt_tuner.py").read_text(encoding="utf-8")
    compiler = (project_root / "tiangong_agent_shell/prompt_compiler.py").read_text(encoding="utf-8")
    assert "tiangong_kernel" not in source
    assert "subprocess" not in source
    assert "while True" not in source
    assert "run_text(" not in source
    assert "execute_plan(" not in source
    assert "import v1" not in (source + compiler).lower()


def main() -> int:
    tests = [
        test_tuner_success_and_leak_update_are_bounded,
        test_attention_gate_uses_homeostasis_bias_without_overriding_hard_boundary,
        test_prompt_compiler_trace_contains_tuning_bias_and_no_prompt_pollution,
        test_run_once_updates_and_persists_tuner_state,
        test_static_no_core_pollution,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("L6.72.15 HomeostasisPromptTuner smoke PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
