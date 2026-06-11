"""L6.72.12 OrganSignalCard smoke tests.

No external network, no real Provider call, no v1 import, no background loop.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("TIANGONG_SOUL_BASELINE_PERSIST", "0")
os.environ.setdefault("TIANGONG_SOUL_BASELINE_PATH", str(Path(tempfile.gettempdir()) / "linyuanzhe_l67212_organ_signal_soul_emotion_baseline.json"))
os.environ.setdefault("TIANGONG_PROMPT_TRACE_FILE", str(Path(tempfile.gettempdir()) / "linyuanzhe_l67212_organ_signal_prompt_trace.jsonl"))
os.environ.setdefault("TIANGONG_PROMPT_TUNER_FILE", str(Path(tempfile.gettempdir()) / "linyuanzhe_l67212_organ_signal_prompt_tuning_state.json"))

from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.organ_signal_card import (
    OrganSignalCard,
    emit_organ_signal_card,
    score_organ_signal_card,
    select_organ_signal_cards,
    trace_organ_signal_cards,
)
from tiangong_agent_shell.prompt_compiler import (
    build_desktop_context,
    compile_prompt,
    trace_prompt_organ_signals,
)
from tiangong_agent_shell.tool_bridge import ToolExecutionMode


def _ready_config() -> ModelConfig:
    return ModelConfig(
        provider="deepseek",
        base_url="https://example.invalid/v1",
        api_key="MOCK_PROVIDER_KEY_SHOULD_REDACT",
        model="deepseek-chat",
        tool_execution_mode=ToolExecutionMode.RUNTIME_GOVERNED,
    )


def test_card_schema_and_kernel_boundary() -> None:
    card = emit_organ_signal_card(
        organ_type="memory",
        summary="用户正在做 L6.72.12，目标是统一器官信号卡，不改核心。",
        source="smoke",
        task_relevance=0.9,
        confidence=0.8,
    )
    data = card.public_dict()
    assert data["schema"] == "tiangong.l6_72_12.organ_signal_card.v1"
    assert data["direct_execution"] is False
    assert data["can_override_kernel"] is False
    assert data["prompt_fragment"] is False
    assert data["organ_type"] == "memory"
    try:
        OrganSignalCard(organ_type="tool", summary="bad", direct_execution=True)
    except ValueError as exc:
        assert "must not execute" in str(exc)
    else:
        raise AssertionError("direct_execution card should be rejected")


def test_attention_gate_suppresses_planner_in_ordinary_chat() -> None:
    planner = emit_organ_signal_card(
        organ_type="planner",
        summary="把普通聊天拆成工具执行计划。",
        source="planner_smoke",
        task_relevance=0.95,
        confidence=0.95,
        utility_history=0.9,
    )
    memory = emit_organ_signal_card(
        organ_type="memory",
        summary="用户偏好少废话、执行力第一。",
        source="memory_smoke",
        task_relevance=0.9,
        confidence=0.85,
        utility_history=0.85,
    )
    selected = select_organ_signal_cards([planner, memory], task_mode="ordinary_chat")
    assert memory in selected
    assert planner not in selected


def test_code_task_prefers_skill_runtime_cards() -> None:
    skill = emit_organ_signal_card(
        organ_type="skill",
        summary="Code-X 修改前必须 compileall，修改后跑 smoke。",
        source="skill_smoke",
        task_relevance=0.88,
        confidence=0.88,
        utility_history=0.9,
    )
    runtime = emit_organ_signal_card(
        organ_type="runtime",
        summary="当前工具由 Runtime 管控，写文件需在工作区内并保留回滚证据。",
        source="runtime_smoke",
        authority_level="runtime",
        task_relevance=0.82,
        confidence=0.86,
        homeostasis_need=0.6,
    )
    emotion = emit_organ_signal_card(
        organ_type="emotion",
        summary="表达风格稍微克制。",
        source="emotion_smoke",
        task_relevance=0.2,
        confidence=0.5,
        noise_score=0.1,
    )
    selected = select_organ_signal_cards([skill, runtime, emotion], task_mode="code_task")
    assert skill in selected
    assert runtime in selected
    assert emotion not in selected
    assert score_organ_signal_card(skill, task_mode="code_task").value > score_organ_signal_card(emotion, task_mode="code_task").value


def test_prompt_compiler_accepts_organ_cards_and_legacy_cards() -> None:
    risk = emit_organ_signal_card(
        organ_type="risk",
        summary="A5 才硬拦；A0-A4 走 Runtime 管控和确认。",
        source="risk_smoke",
        authority_level="runtime",
        task_relevance=0.86,
        confidence=0.9,
        utility_history=0.8,
    )
    ctx = build_desktop_context(
        _ready_config(),
        task_mode="code_task",
        organ_signal_cards=[risk],
        memory_cards=["项目口径：LLM 是主脑，临渊者是外骨骼。"],
        skill_cards=["Code-X 任务必须输出修改点、验证结果、回滚说明。"],
    )
    bundle = compile_prompt(ctx)
    prompt = bundle.system_prompt
    assert "[OrganSignalCards / 器官信号卡]" in prompt
    assert "RiskCard" in prompt
    assert "MemoryCard" in prompt
    assert "SkillCard" in prompt
    assert "不得覆盖 Kernel" in prompt
    assert "最小 CLI 模式" not in prompt
    trace = trace_prompt_organ_signals(ctx)
    assert trace and all("card" in row and "score" in row for row in trace)


def test_secret_redaction_and_trace_only_not_injected() -> None:
    secret = emit_organ_signal_card(
        organ_type="provider",
        summary="api_key=MOCK_PROVIDER_SECRET_SHOULD_REDACT",
        source="provider_smoke",
        task_relevance=0.9,
        confidence=0.9,
    )
    assert secret.summary == "[redacted-sensitive-summary]"
    trace_only = emit_organ_signal_card(
        organ_type="audit",
        summary="内部审计行，只能进 trace。",
        source="audit_smoke",
        visibility="trace_only",
        task_relevance=1.0,
        confidence=1.0,
    )
    ctx = build_desktop_context(_ready_config(), organ_signal_cards=[trace_only])
    prompt = compile_prompt(ctx).system_prompt
    assert "内部审计行" not in prompt
    trace = trace_organ_signal_cards([trace_only], task_mode="ordinary_chat")
    assert trace[0]["score"]["reason"] == "trace_only"


def test_static_no_core_pollution() -> None:
    project_root = Path(__file__).resolve().parent
    compiler = (project_root / "tiangong_agent_shell/prompt_compiler.py").read_text(encoding="utf-8")
    card = (project_root / "tiangong_agent_shell/organ_signal_card.py").read_text(encoding="utf-8")
    assert "tiangong_kernel" not in card
    assert "while True" not in card
    assert "subprocess" not in card
    assert "import v1" not in (compiler + card).lower()


def main() -> int:
    tests = [
        test_card_schema_and_kernel_boundary,
        test_attention_gate_suppresses_planner_in_ordinary_chat,
        test_code_task_prefers_skill_runtime_cards,
        test_prompt_compiler_accepts_organ_cards_and_legacy_cards,
        test_secret_redaction_and_trace_only_not_injected,
        test_static_no_core_pollution,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("L6.72.12 OrganSignalCard smoke PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
