"""L6.72.16 HomeostasisPromptTuner / 稳态、反锁死、基线对照版。

本模块把 PromptTrace outcome 转换为 AttentionGate 的小步调权状态。它只
影响 PromptCompiler 选择哪些 OrganSignalCard 进入上下文；不执行工具、不写
器官、不改 Runtime 主链、不覆盖 Kernel。

L6.72.16 补强点：
- EMA 保持 clamp 与小步学习，防止数值发散。
- 增加 baseline/tuned 影子成功率，用于检测调权是否低于基线。
- 增加选择多样性 EMA、最大器官占比 EMA 和 dominance streak。
- 长期低多样性或 tuned 低于 baseline 时，压缩正向偏置并开启 lock guard。
- 任意异常都退回基线，不阻断聊天或执行链。
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .composition_root import AgentShellContext
    from .organ_signal_card import OrganSignalCard


L6_72_16_PROMPT_TUNER_SCHEMA = "tiangong.l6_72_16.homeostasis_prompt_tuner.v2"
# 兼容旧 smoke 与旧导入点：常量名保留，但值指向新版 schema。
L6_72_15_PROMPT_TUNER_SCHEMA = L6_72_16_PROMPT_TUNER_SCHEMA
_ALLOWED_TASK_MODES = {"ordinary_chat", "tool_task", "code_task", "file_task", "diagnostic_task"}
_ALLOWED_ORGANS = {
    "memory",
    "skill",
    "emotion",
    "runtime",
    "tool",
    "planner",
    "risk",
    "self_heal",
    "lifecycle",
    "provider",
    "ui",
    "audit",
    "handoff",
    "context",
    "unknown",
}


@dataclass(frozen=True)
class HomeostasisPromptTuningState:
    """PromptCore 的稳态调权状态。

    ``organ_bias`` 的单位是 AttentionGate 分值偏置，范围限制在 [-0.35, 0.35]。
    ``global_threshold_delta`` 用于抬高/降低入选阈值，防止噪声或冲突扩散。
    L6.72.16 只在上下文适配层保存状态，不修改任何器官或 Runtime。
    """

    schema: str = L6_72_16_PROMPT_TUNER_SCHEMA
    version: int = 2
    state_id: str = field(default_factory=lambda: uuid4().hex[:16])
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sample_count: int = 0
    success_ema: float = 0.50
    failure_ema: float = 0.00
    noise_pressure: float = 0.00
    conflict_pressure: float = 0.00
    planner_leak_pressure: float = 0.00
    provider_pressure: float = 0.00
    global_threshold_delta: float = 0.00
    organ_bias: Mapping[str, float] = field(default_factory=dict)
    # L6.72.16 baseline / anti-lock fields.
    baseline_success_ema: float = 0.50
    tuned_success_ema: float = 0.50
    quality_delta_ema: float = 0.00
    diversity_entropy_ema: float = 1.00
    max_organ_ratio_ema: float = 0.00
    selection_dominance_streak: int = 0
    negative_delta_streak: int = 0
    exploration_rate: float = 0.06
    lock_guard_active: bool = False
    rollback_reason: str = ""
    rollback_available: bool = True
    frozen: bool = False
    last_feedback_summary: str = "baseline"

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "version": int(self.version),
            "state_id": self.state_id,
            "updated_at": self.updated_at,
            "sample_count": int(self.sample_count),
            "success_ema": _round(self.success_ema),
            "failure_ema": _round(self.failure_ema),
            "noise_pressure": _round(self.noise_pressure),
            "conflict_pressure": _round(self.conflict_pressure),
            "planner_leak_pressure": _round(self.planner_leak_pressure),
            "provider_pressure": _round(self.provider_pressure),
            "global_threshold_delta": _round(self.global_threshold_delta),
            "organ_bias": {str(k): _round(v) for k, v in dict(self.organ_bias).items()},
            "baseline_success_ema": _round(self.baseline_success_ema),
            "tuned_success_ema": _round(self.tuned_success_ema),
            "quality_delta_ema": _round(self.quality_delta_ema),
            "diversity_entropy_ema": _round(self.diversity_entropy_ema),
            "max_organ_ratio_ema": _round(self.max_organ_ratio_ema),
            "selection_dominance_streak": int(self.selection_dominance_streak),
            "negative_delta_streak": int(self.negative_delta_streak),
            "exploration_rate": _round(self.exploration_rate),
            "lock_guard_active": bool(self.lock_guard_active),
            "rollback_reason": _safe_text(self.rollback_reason, 240),
            "rollback_available": bool(self.rollback_available),
            "frozen": bool(self.frozen),
            "last_feedback_summary": _safe_text(self.last_feedback_summary, 240),
        }


def baseline_prompt_tuning_state() -> HomeostasisPromptTuningState:
    return HomeostasisPromptTuningState()


def coerce_prompt_tuning_state(raw: Mapping[str, Any] | HomeostasisPromptTuningState | None) -> HomeostasisPromptTuningState:
    if isinstance(raw, HomeostasisPromptTuningState):
        return raw
    if not isinstance(raw, Mapping):
        return baseline_prompt_tuning_state()
    try:
        organ_bias = {
            _normalize_organ(key): _clamp(float(value), -0.35, 0.35)
            for key, value in dict(raw.get("organ_bias", {}) or {}).items()
        }
        # 兼容 L6.72.15：没有 baseline/tuned 字段时沿用 success_ema。
        success_ema = _clamp(float(raw.get("success_ema", 0.5) or 0.5), 0.0, 1.0)
        baseline_success = _clamp(float(raw.get("baseline_success_ema", success_ema) or success_ema), 0.0, 1.0)
        tuned_success = _clamp(float(raw.get("tuned_success_ema", success_ema) or success_ema), 0.0, 1.0)
        return HomeostasisPromptTuningState(
            schema=L6_72_16_PROMPT_TUNER_SCHEMA,
            version=max(2, int(raw.get("version", 2) or 2)),
            state_id=_safe_text(raw.get("state_id", ""), 32) or uuid4().hex[:16],
            updated_at=_safe_text(raw.get("updated_at", ""), 64) or datetime.now(timezone.utc).isoformat(),
            sample_count=max(0, int(raw.get("sample_count", 0) or 0)),
            success_ema=success_ema,
            failure_ema=_clamp(float(raw.get("failure_ema", 0.0) or 0.0), 0.0, 1.0),
            noise_pressure=_clamp(float(raw.get("noise_pressure", 0.0) or 0.0), 0.0, 1.0),
            conflict_pressure=_clamp(float(raw.get("conflict_pressure", 0.0) or 0.0), 0.0, 1.0),
            planner_leak_pressure=_clamp(float(raw.get("planner_leak_pressure", 0.0) or 0.0), 0.0, 1.0),
            provider_pressure=_clamp(float(raw.get("provider_pressure", 0.0) or 0.0), 0.0, 1.0),
            global_threshold_delta=_clamp(float(raw.get("global_threshold_delta", 0.0) or 0.0), -0.35, 0.45),
            organ_bias=organ_bias,
            baseline_success_ema=baseline_success,
            tuned_success_ema=tuned_success,
            quality_delta_ema=_clamp(float(raw.get("quality_delta_ema", tuned_success - baseline_success) or 0.0), -1.0, 1.0),
            diversity_entropy_ema=_clamp(float(raw.get("diversity_entropy_ema", 1.0) or 1.0), 0.0, 1.0),
            max_organ_ratio_ema=_clamp(float(raw.get("max_organ_ratio_ema", 0.0) or 0.0), 0.0, 1.0),
            selection_dominance_streak=max(0, int(raw.get("selection_dominance_streak", 0) or 0)),
            negative_delta_streak=max(0, int(raw.get("negative_delta_streak", 0) or 0)),
            exploration_rate=_clamp(float(raw.get("exploration_rate", 0.06) or 0.06), 0.0, 0.18),
            lock_guard_active=bool(raw.get("lock_guard_active", False)),
            rollback_reason=_safe_text(raw.get("rollback_reason", ""), 240),
            rollback_available=bool(raw.get("rollback_available", True)),
            frozen=bool(raw.get("frozen", False)),
            last_feedback_summary=_safe_text(raw.get("last_feedback_summary", ""), 240),
        )
    except Exception:
        return baseline_prompt_tuning_state()


def get_prompt_tuning_state(shell_context: "AgentShellContext" | None = None) -> HomeostasisPromptTuningState:
    """读取当前稳态调权状态；失败退回基线。"""
    if shell_context is not None:
        state = getattr(shell_context, "prompt_tuning_state", None)
        if state is not None:
            return coerce_prompt_tuning_state(state)
    loaded = _load_state(shell_context)
    if shell_context is not None:
        setattr(shell_context, "prompt_tuning_state", loaded)
    return loaded


def update_prompt_tuning_from_outcome(
    shell_context: "AgentShellContext" | None,
    outcome: Mapping[str, Any] | None,
) -> HomeostasisPromptTuningState:
    """根据本轮 outcome 小步更新调权状态；不阻断主流程。"""
    prior = get_prompt_tuning_state(shell_context)
    updated = tune_prompt_state_from_outcome(prior, outcome or {})
    if shell_context is not None:
        setattr(shell_context, "prompt_tuning_state", updated)
        _persist_state(shell_context, updated)
        _append_tuner_event(shell_context, updated, outcome or {})
    return updated


def tune_prompt_state_from_outcome(
    prior: HomeostasisPromptTuningState | Mapping[str, Any] | None,
    outcome: Mapping[str, Any] | None,
    *,
    learning_rate: float = 0.055,
) -> HomeostasisPromptTuningState:
    """从 PromptTrace outcome 推导下一版稳态权重。"""
    state = coerce_prompt_tuning_state(prior)
    if state.frozen or str(os.getenv("TIANGONG_PROMPT_TUNER_DISABLED", "")).strip().lower() in {"1", "true", "yes", "on"}:
        return state
    record = dict(outcome or {})
    success = 1.0 if bool(record.get("success_proxy")) else 0.0
    model_ok = bool(record.get("model_ok"))
    planner_leak = 1.0 if bool(record.get("planner_leak_detected")) else 0.0
    internal_log_leak = 1.0 if bool(record.get("internal_log_leak_detected")) else 0.0
    provider_not_configured = 1.0 if bool(record.get("provider_not_configured")) else 0.0
    empty_answer = 1.0 if bool(record.get("empty_answer")) else 0.0
    failed = 1.0 if not success else 0.0

    # baseline 影子对照：真实 A/B 未开启时默认与 tuned 同步；测试/回放可显式传入 baseline_shadow_success_proxy。
    if "baseline_shadow_success_proxy" in record:
        baseline_success = 1.0 if bool(record.get("baseline_shadow_success_proxy")) else 0.0
    else:
        baseline_success = success

    selected_counts = _coerce_counts(record.get("selected_organ_counts", {}))
    if not selected_counts:
        selected_counts = {str(k): 1 for k in _as_mapping(record.get("credit_by_organ", {})).keys()}
    entropy, max_ratio = _selection_diversity(selected_counts)
    diversity_problem = bool(sum(selected_counts.values()) >= 4 and (max_ratio >= 0.60 or entropy < 0.45))

    success_ema = _ema(state.success_ema, success, 0.12)
    tuned_success_ema = _ema(state.tuned_success_ema, success, 0.12)
    baseline_success_ema = _ema(state.baseline_success_ema, baseline_success, 0.12)
    quality_delta_ema = _ema_raw(state.quality_delta_ema, success - baseline_success, 0.10, -1.0, 1.0)
    failure_ema = _ema(state.failure_ema, failed, 0.12)
    noise_pressure = _clamp(_ema(state.noise_pressure, max(planner_leak, internal_log_leak, empty_answer), 0.18), 0.0, 1.0)
    conflict_pressure = _clamp(_ema(state.conflict_pressure, 1.0 if bool(record.get("plan_failed_fallback")) else 0.0, 0.12), 0.0, 1.0)
    planner_pressure = _clamp(_ema(state.planner_leak_pressure, planner_leak, 0.22), 0.0, 1.0)
    provider_pressure = _clamp(_ema(state.provider_pressure, provider_not_configured, 0.18), 0.0, 1.0)
    diversity_entropy_ema = _ema(state.diversity_entropy_ema, entropy, 0.18)
    max_organ_ratio_ema = _ema(state.max_organ_ratio_ema, max_ratio, 0.18)

    dominance_streak = state.selection_dominance_streak + 1 if diversity_problem else max(0, state.selection_dominance_streak - 1)
    delta_bad = bool((tuned_success_ema < baseline_success_ema - 0.03) or (quality_delta_ema < -0.03))
    negative_delta_streak = state.negative_delta_streak + 1 if delta_bad else max(0, state.negative_delta_streak - 1)

    organ_bias = dict(state.organ_bias)
    credit_by_organ = _as_mapping(record.get("credit_by_organ", {}))
    for organ, credit in credit_by_organ.items():
        name = _normalize_organ(organ)
        try:
            signal = float(credit)
        except (TypeError, ValueError):
            continue
        old = float(organ_bias.get(name, 0.0))
        organ_bias[name] = _clamp(0.92 * old + learning_rate * signal, -0.35, 0.35)

    if planner_leak:
        organ_bias["planner"] = _clamp(float(organ_bias.get("planner", 0.0)) - 0.16, -0.35, 0.35)
        organ_bias["runtime"] = _clamp(float(organ_bias.get("runtime", 0.0)) - 0.04, -0.35, 0.35)
    if internal_log_leak:
        for organ in ("audit", "runtime", "planner"):
            organ_bias[organ] = _clamp(float(organ_bias.get(organ, 0.0)) - 0.08, -0.35, 0.35)
    if provider_not_configured:
        organ_bias["provider"] = _clamp(float(organ_bias.get("provider", 0.0)) - 0.06, -0.35, 0.35)
    if success:
        # 成功后轻微释放阈值压力，但不放大噪声卡。
        for organ in list(organ_bias):
            organ_bias[organ] = _clamp(0.985 * float(organ_bias[organ]), -0.35, 0.35)

    diversity_pressure = (1.0 - diversity_entropy_ema) * 0.16 + max(0.0, max_organ_ratio_ema - 0.55) * 0.22
    threshold_delta = _clamp(
        0.28 * noise_pressure
        + 0.18 * conflict_pressure
        + 0.22 * planner_pressure
        + 0.10 * provider_pressure
        + diversity_pressure
        - 0.10 * success_ema,
        -0.12,
        0.45,
    )

    rollback_reason = ""
    lock_guard = bool(state.lock_guard_active)
    sample_count = state.sample_count + 1
    # 连续失败或泄漏时触发稳态保护：抬高阈值并衰减正向偏置。
    if state.sample_count >= 3 and failure_ema > 0.78 and noise_pressure > 0.55:
        organ_bias = {key: _clamp(value * 0.45, -0.18, 0.18) for key, value in organ_bias.items()}
        threshold_delta = max(threshold_delta, 0.30)
        lock_guard = True
        rollback_reason = "noise_failure_protection"

    # tuned 低于 baseline：不等待完全崩溃，先压缩正向偏置。
    if sample_count >= 50 and (tuned_success_ema < baseline_success_ema - 0.03 or negative_delta_streak >= 8):
        organ_bias = {key: _clamp(value * 0.35, -0.14, 0.14) for key, value in organ_bias.items()}
        threshold_delta = max(threshold_delta, 0.16)
        lock_guard = True
        rollback_reason = rollback_reason or "tuned_under_baseline"

    # 多样性退化：冻结正反馈，只允许小范围偏置，交给选卡层配额恢复多器官输入。
    if dominance_streak >= 20 or (sample_count >= 30 and diversity_entropy_ema < 0.42 and max_organ_ratio_ema > 0.62):
        organ_bias = {key: _clamp(value, -0.24, 0.16 if value > 0 else 0.0) for key, value in organ_bias.items()}
        threshold_delta = max(threshold_delta, 0.10)
        lock_guard = True
        rollback_reason = rollback_reason or "diversity_lock_guard"

    # lock guard 关闭条件：成功率恢复且多样性恢复一段时间后自动解除。
    if lock_guard and not rollback_reason and success_ema > 0.70 and diversity_entropy_ema > 0.62 and max_organ_ratio_ema < 0.52:
        lock_guard = False

    exploration_rate = _clamp(0.06 + 0.06 * (1.0 if lock_guard else 0.0) + 0.04 * max(0.0, 0.55 - diversity_entropy_ema), 0.03, 0.16)
    summary = _safe_text(record.get("feedback_summary", ""), 240) or ("success" if success else "failure")
    if rollback_reason:
        summary = f"{summary}；tuner_guard={rollback_reason}"

    return HomeostasisPromptTuningState(
        version=2,
        state_id=uuid4().hex[:16],
        updated_at=datetime.now(timezone.utc).isoformat(),
        sample_count=sample_count,
        success_ema=success_ema,
        failure_ema=failure_ema,
        noise_pressure=noise_pressure,
        conflict_pressure=conflict_pressure,
        planner_leak_pressure=planner_pressure,
        provider_pressure=provider_pressure,
        global_threshold_delta=threshold_delta,
        organ_bias=organ_bias,
        baseline_success_ema=baseline_success_ema,
        tuned_success_ema=tuned_success_ema,
        quality_delta_ema=quality_delta_ema,
        diversity_entropy_ema=diversity_entropy_ema,
        max_organ_ratio_ema=max_organ_ratio_ema,
        selection_dominance_streak=dominance_streak,
        negative_delta_streak=negative_delta_streak,
        exploration_rate=exploration_rate,
        lock_guard_active=lock_guard,
        rollback_reason=rollback_reason or (state.rollback_reason if lock_guard else ""),
        rollback_available=True,
        frozen=False,
        last_feedback_summary=summary,
    )


def tuned_score_bias(
    card: "OrganSignalCard" | Mapping[str, Any],
    *,
    task_mode: str = "ordinary_chat",
    tuning_state: Mapping[str, Any] | HomeostasisPromptTuningState | None = None,
) -> float:
    """返回单张卡的稳态分值偏置。普通聊天 Planner 仍由硬规则阻断。"""
    state = coerce_prompt_tuning_state(tuning_state)
    organ = _card_organ(card)
    if _normalize_task(task_mode) == "ordinary_chat" and organ == "planner":
        return -9.0
    base = float(dict(state.organ_bias).get(organ, 0.0))
    if state.lock_guard_active and base > 0:
        base *= 0.55
    if state.max_organ_ratio_ema > 0.62 and base > 0:
        base -= 0.04 + 0.08 * (state.max_organ_ratio_ema - 0.62)
    noise = _card_float(card, "noise_score", "noise")
    conflict = _card_float(card, "conflict_score", "conflict")
    risk = _card_float(card, "risk_score", "risk")
    cost = _card_float(card, "token_cost")
    bias = base
    bias -= state.noise_pressure * (0.22 * noise + 0.05 * cost)
    bias -= state.conflict_pressure * (0.20 * conflict)
    bias -= state.planner_leak_pressure * (0.22 if organ == "planner" else 0.0)
    if _normalize_task(task_mode) == "ordinary_chat" and organ in {"tool", "runtime", "audit"}:
        bias -= state.noise_pressure * 0.04
    if organ == "risk" and risk >= 0.70:
        bias += 0.04
    return round(_clamp(bias, -0.65, 0.45), 6)


def tuned_min_score(
    *,
    task_mode: str = "ordinary_chat",
    base_min_score: float = 1.60,
    tuning_state: Mapping[str, Any] | HomeostasisPromptTuningState | None = None,
) -> float:
    state = coerce_prompt_tuning_state(tuning_state)
    task = _normalize_task(task_mode)
    delta = float(state.global_threshold_delta)
    if task == "ordinary_chat":
        delta += 0.05 * state.planner_leak_pressure
    elif task in {"code_task", "tool_task", "file_task", "diagnostic_task"}:
        delta -= 0.04 * state.success_ema
    if state.lock_guard_active:
        delta += 0.03
    return round(_clamp(float(base_min_score) + delta, 1.20, 2.20), 6)


def prompt_tuning_public_summary(shell_context: "AgentShellContext" | None = None) -> dict[str, Any]:
    return get_prompt_tuning_state(shell_context).public_dict()


def reset_prompt_tuning_state(shell_context: "AgentShellContext" | None = None) -> HomeostasisPromptTuningState:
    state = baseline_prompt_tuning_state()
    if shell_context is not None:
        setattr(shell_context, "prompt_tuning_state", state)
        _persist_state(shell_context, state)
    return state


def _load_state(shell_context: "AgentShellContext" | None) -> HomeostasisPromptTuningState:
    path = _state_file_path(shell_context)
    if path is None or not path.exists():
        return baseline_prompt_tuning_state()
    try:
        return coerce_prompt_tuning_state(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return baseline_prompt_tuning_state()


def _persist_state(shell_context: "AgentShellContext", state: HomeostasisPromptTuningState) -> None:
    if str(os.getenv("TIANGONG_PROMPT_TUNER_DISABLED", "")).strip().lower() in {"1", "true", "yes", "on"}:
        return
    path = _state_file_path(shell_context)
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state.public_dict(), ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    except Exception:
        return


def _append_tuner_event(shell_context: "AgentShellContext", state: HomeostasisPromptTuningState, outcome: Mapping[str, Any]) -> None:
    path = _events_file_path(shell_context)
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "schema": L6_72_16_PROMPT_TUNER_SCHEMA + ".event",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace_id": _safe_text(outcome.get("trace_id", ""), 40) if isinstance(outcome, Mapping) else "",
            "success_proxy": bool(outcome.get("success_proxy")) if isinstance(outcome, Mapping) else False,
            "baseline_shadow_success_proxy": bool(outcome.get("baseline_shadow_success_proxy")) if isinstance(outcome, Mapping) and "baseline_shadow_success_proxy" in outcome else None,
            "planner_leak_detected": bool(outcome.get("planner_leak_detected")) if isinstance(outcome, Mapping) else False,
            "internal_log_leak_detected": bool(outcome.get("internal_log_leak_detected")) if isinstance(outcome, Mapping) else False,
            "selected_organ_counts": dict(_coerce_counts(outcome.get("selected_organ_counts", {}))) if isinstance(outcome, Mapping) else {},
            "state": state.public_dict(),
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    except Exception:
        return


def _state_file_path(shell_context: "AgentShellContext" | None) -> Path | None:
    env_path = os.getenv("TIANGONG_PROMPT_TUNER_FILE", "").strip()
    if env_path:
        return Path(env_path).expanduser().resolve()
    workspace = getattr(shell_context, "workspace", None) if shell_context is not None else None
    if workspace is None:
        return None
    try:
        return Path(workspace).expanduser().resolve() / ".linyuanzhe" / "prompt_trace" / "prompt_tuning_state.json"
    except Exception:
        return None


def _events_file_path(shell_context: "AgentShellContext" | None) -> Path | None:
    state_path = _state_file_path(shell_context)
    if state_path is None:
        return None
    return state_path.with_name("prompt_tuning_events.jsonl")


def _card_organ(card: "OrganSignalCard" | Mapping[str, Any]) -> str:
    if isinstance(card, Mapping):
        return _normalize_organ(card.get("organ_type", "unknown"))
    return _normalize_organ(getattr(card, "organ_type", "unknown"))


def _card_float(card: "OrganSignalCard" | Mapping[str, Any], *names: str) -> float:
    for name in names:
        raw = card.get(name) if isinstance(card, Mapping) else getattr(card, name, None)
        if raw is None:
            continue
        try:
            return _clamp(float(raw), 0.0, 1.0)
        except (TypeError, ValueError):
            continue
    return 0.0


def _normalize_organ(value: Any) -> str:
    clean = str(value or "unknown").strip().lower().replace("-", "_")
    return clean if clean in _ALLOWED_ORGANS else "unknown"


def _normalize_task(value: Any) -> str:
    clean = str(value or "ordinary_chat").strip().lower().replace("-", "_")
    return clean if clean in _ALLOWED_TASK_MODES else "ordinary_chat"


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _coerce_counts(value: Any) -> dict[str, int]:
    if not isinstance(value, Mapping):
        return {}
    counts: dict[str, int] = {}
    for key, raw in value.items():
        organ = _normalize_organ(key)
        try:
            number = int(raw)
        except (TypeError, ValueError):
            number = 0
        if number > 0:
            counts[organ] = counts.get(organ, 0) + number
    return counts


def _selection_diversity(counts: Mapping[str, int]) -> tuple[float, float]:
    total = sum(max(0, int(v)) for v in counts.values())
    if total <= 0:
        return 1.0, 0.0
    positive = [max(0, int(v)) for v in counts.values() if int(v) > 0]
    if len(positive) <= 1:
        return 0.0, 1.0
    entropy = 0.0
    for count in positive:
        p = count / total
        entropy -= p * math.log(p)
    normalized_entropy = entropy / math.log(len(positive)) if len(positive) > 1 else 0.0
    max_ratio = max(positive) / total
    return _clamp(normalized_entropy, 0.0, 1.0), _clamp(max_ratio, 0.0, 1.0)


def _ema(old: float, new: float, rate: float) -> float:
    return _clamp((1.0 - rate) * float(old) + rate * float(new), 0.0, 1.0)


def _ema_raw(old: float, new: float, rate: float, low: float, high: float) -> float:
    return _clamp((1.0 - rate) * float(old) + rate * float(new), low, high)


def _clamp(value: float, low: float, high: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = low
    if number != number:
        number = low
    return max(low, min(high, number))


def _round(value: Any) -> float:
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return 0.0


def _safe_text(value: Any, limit: int) -> str:
    text = str(value or "").replace("\x00", " ").replace("\r", " ").strip()
    text = " ".join(part.strip() for part in text.splitlines() if part.strip())
    return text[: max(16, int(limit))]
