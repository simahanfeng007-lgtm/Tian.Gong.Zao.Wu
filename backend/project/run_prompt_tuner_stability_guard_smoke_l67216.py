"""L6.72.16 PromptTuner 稳定性 / 反锁死 / 基线对照 smoke。

No external network, no real Provider call, no v1 import, no background loop.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from tiangong_agent_shell.homeostasis_prompt_tuner import (
    L6_72_16_PROMPT_TUNER_SCHEMA,
    baseline_prompt_tuning_state,
    tune_prompt_state_from_outcome,
)
from tiangong_agent_shell.organ_signal_card import emit_organ_signal_card, select_organ_signal_cards


def _memory_cards(n: int):
    return [
        emit_organ_signal_card(
            organ_type="memory",
            summary=f"memory card {i}",
            source="stability_smoke",
            task_relevance=0.92,
            confidence=0.86,
            utility_history=0.92,
        )
        for i in range(n)
    ]


def _mixed_cards():
    cards = _memory_cards(10)
    for organ in ("risk", "ui", "provider", "emotion", "skill", "runtime", "tool", "context"):
        cards.append(
            emit_organ_signal_card(
                organ_type=organ,
                summary=f"{organ} card",
                source="stability_smoke",
                task_relevance=0.72,
                confidence=0.80,
                utility_history=0.74,
                risk_score=0.72 if organ == "risk" else 0.0,
            )
        )
    return cards


def test_long_run_ema_is_bounded_and_schema_v2() -> None:
    state = baseline_prompt_tuning_state()
    for _ in range(500):
        state = tune_prompt_state_from_outcome(
            state,
            {
                "success_proxy": True,
                "baseline_shadow_success_proxy": True,
                "model_ok": True,
                "credit_by_organ": {"memory": 1.0},
                "selected_organ_counts": {"memory": 2, "risk": 1, "ui": 1, "provider": 1},
            },
        )
    data = state.public_dict()
    assert data["schema"] == L6_72_16_PROMPT_TUNER_SCHEMA
    assert data["sample_count"] == 500
    assert 0.0 <= data["success_ema"] <= 1.0
    assert -0.35 <= data["organ_bias"]["memory"] <= 0.35
    assert 1.20 <= 1.60 + data["global_threshold_delta"] <= 2.20


def test_ordinary_chat_diversity_guard_blocks_memory_takeover() -> None:
    state = baseline_prompt_tuning_state()
    for _ in range(500):
        state = tune_prompt_state_from_outcome(
            state,
            {
                "success_proxy": True,
                "baseline_shadow_success_proxy": True,
                "model_ok": True,
                "credit_by_organ": {"memory": 1.0},
                "selected_organ_counts": {"memory": 8},
                "feedback_summary": "simulated memory-only success",
            },
        )
    selected = select_organ_signal_cards(_mixed_cards(), task_mode="ordinary_chat", tuning_state=state.public_dict(), max_cards=8)
    counts = Counter(card.organ_type for card in selected)
    assert counts["memory"] <= 2
    assert counts["risk"] >= 1
    assert len(counts) >= 3
    assert state.public_dict()["lock_guard_active"] is True


def test_code_task_required_organs_survive_positive_memory_bias() -> None:
    state = baseline_prompt_tuning_state()
    for _ in range(120):
        state = tune_prompt_state_from_outcome(
            state,
            {
                "success_proxy": True,
                "baseline_shadow_success_proxy": True,
                "model_ok": True,
                "credit_by_organ": {"memory": 1.0},
                "selected_organ_counts": {"memory": 5, "skill": 1, "runtime": 1, "tool": 1},
            },
        )
    cards = _memory_cards(8)
    for organ in ("runtime", "tool", "skill", "risk", "self_heal"):
        cards.append(
            emit_organ_signal_card(
                organ_type=organ,
                summary=f"{organ} required card",
                source="code_guard_smoke",
                task_relevance=0.76,
                confidence=0.82,
                utility_history=0.72,
                risk_score=0.72 if organ == "risk" else 0.0,
            )
        )
    selected = select_organ_signal_cards(cards, task_mode="code_task", tuning_state=state.public_dict(), max_cards=8)
    organs = {card.organ_type for card in selected}
    counts = Counter(card.organ_type for card in selected)
    assert {"runtime", "tool", "skill", "risk"}.issubset(organs)
    assert counts["memory"] <= 2


def test_tuned_under_baseline_triggers_rollback_guard() -> None:
    state = baseline_prompt_tuning_state()
    for _ in range(60):
        state = tune_prompt_state_from_outcome(
            state,
            {
                "success_proxy": False,
                "baseline_shadow_success_proxy": True,
                "model_ok": True,
                "empty_answer": False,
                "credit_by_organ": {"memory": -0.4},
                "selected_organ_counts": {"memory": 8},
            },
        )
    data = state.public_dict()
    assert data["baseline_success_ema"] > data["tuned_success_ema"]
    assert data["lock_guard_active"] is True
    assert data["rollback_reason"] in {"tuned_under_baseline", "diversity_lock_guard", "noise_failure_protection"}
    assert data["global_threshold_delta"] >= 0.10


def test_static_no_core_pollution() -> None:
    project_root = Path(__file__).resolve().parent
    source = (project_root / "tiangong_agent_shell/homeostasis_prompt_tuner.py").read_text(encoding="utf-8")
    selector = (project_root / "tiangong_agent_shell/organ_signal_card.py").read_text(encoding="utf-8")
    assert "tiangong_kernel" not in source
    assert "subprocess" not in source
    assert "while True" not in source
    assert "run_text(" not in source
    assert "execute_plan(" not in source
    assert "import v1" not in (source + selector).lower()


def main() -> int:
    tests = [
        test_long_run_ema_is_bounded_and_schema_v2,
        test_ordinary_chat_diversity_guard_blocks_memory_takeover,
        test_code_task_required_organs_survive_positive_memory_bias,
        test_tuned_under_baseline_triggers_rollback_guard,
        test_static_no_core_pollution,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("L6.72.16 PromptTuner stability guard smoke PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
