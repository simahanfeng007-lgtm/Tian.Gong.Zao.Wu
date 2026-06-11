"""L6.72.16 PromptTrace / 器官信号反馈归因 + 稳态调权回写。

本模块记录 PromptCompiler 每轮选择了哪些器官信号卡、拒绝了哪些卡，
并在模型/回退结果产生后追加 outcome 记录，用于后续动态调权。

设计边界：
- 只做脱敏记录和归因摘要，不进入 LLM system prompt，不进入用户回复。
- 不执行工具、不写记忆、不改 Runtime 主链、不启动后台循环。
- trace 写入失败必须静默降级，不能阻断聊天或执行链。
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, TYPE_CHECKING
from uuid import uuid4

from .safe_logging import redact_text

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .composition_root import AgentShellContext
    from .prompt_compiler import PromptBundle, PromptContext


L6_72_14_PROMPT_TRACE_SCHEMA = "tiangong.l6_72_14.prompt_trace.v1"
L6_72_14_PROMPT_OUTCOME_SCHEMA = "tiangong.l6_72_14.prompt_trace_outcome.v1"

_LEAK_MARKERS = (
    "[计划器]",
    "【计划器】",
    "[运行链]",
    "【运行链】",
    "未生成可执行计划",
    "plan_failed",
    "PromptTrace",
)
_INTERNAL_LOG_MARKERS = (
    "Traceback (most recent call last)",
    "stderr",
    "RuntimeLog",
    "PromptTrace",
    "[错误]",
    "【错误】",
)


@dataclass(frozen=True)
class PromptTraceEvent:
    """单轮 Prompt 编译轨迹。"""

    trace_id: str
    timestamp: str
    session_id: str
    task_mode: str
    entry_channel: str
    provider_ready: bool
    user_message_digest: str
    prompt_hash: str
    system_prompt_chars: int
    cards_total: int
    selected_card_ids: tuple[str, ...]
    rejected_card_ids: tuple[str, ...]
    selected_organ_counts: Mapping[str, int]
    rejected_reason_counts: Mapping[str, int]
    card_trace_rows: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_72_14_PROMPT_TRACE_SCHEMA,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "task_mode": self.task_mode,
            "entry_channel": self.entry_channel,
            "provider_ready": self.provider_ready,
            "user_message_digest": self.user_message_digest,
            "prompt_hash": self.prompt_hash,
            "system_prompt_chars": self.system_prompt_chars,
            "cards_total": self.cards_total,
            "selected_card_ids": list(self.selected_card_ids),
            "rejected_card_ids": list(self.rejected_card_ids),
            "selected_organ_counts": dict(self.selected_organ_counts),
            "rejected_reason_counts": dict(self.rejected_reason_counts),
            "card_trace_rows": list(self.card_trace_rows),
            "outcome_pending": True,
        }


def build_prompt_trace_event(
    *,
    session_id: str,
    prompt_context: "PromptContext",
    prompt_bundle: "PromptBundle",
    user_text: str,
    card_trace_rows: Iterable[Mapping[str, Any]],
) -> PromptTraceEvent:
    """构造脱敏 PromptTraceEvent，不产生副作用。"""
    rows = tuple(_sanitize_trace_rows(card_trace_rows))
    selected_ids: list[str] = []
    rejected_ids: list[str] = []
    selected_organs: Counter[str] = Counter()
    rejected_reasons: Counter[str] = Counter()
    for row in rows:
        card = row.get("card", {}) if isinstance(row.get("card"), Mapping) else {}
        score = row.get("score", {}) if isinstance(row.get("score"), Mapping) else {}
        card_id = str(card.get("card_id") or "")
        organ = str(card.get("organ_type") or "unknown")
        if bool(score.get("selected")):
            selected_ids.append(card_id)
            selected_organs[organ] += 1
        else:
            rejected_ids.append(card_id)
            rejected_reasons[str(score.get("reason") or "not_selected")] += 1
    prompt_text = str(getattr(prompt_bundle, "system_prompt", "") or "")
    return PromptTraceEvent(
        trace_id=uuid4().hex,
        timestamp=_utc_now(),
        session_id=_safe_id(session_id),
        task_mode=str(getattr(prompt_context, "task_mode", "ordinary_chat") or "ordinary_chat"),
        entry_channel=str(getattr(prompt_context, "entry_channel", "cli") or "cli"),
        provider_ready=bool(getattr(getattr(prompt_context, "provider_state", None), "is_real_model_ready", False)),
        user_message_digest=_digest_text(user_text),
        prompt_hash=_digest_text(prompt_text),
        system_prompt_chars=len(prompt_text),
        cards_total=len(rows),
        selected_card_ids=tuple(selected_ids),
        rejected_card_ids=tuple(rejected_ids),
        selected_organ_counts=dict(selected_organs),
        rejected_reason_counts=dict(rejected_reasons),
        card_trace_rows=rows,
    )


def record_prompt_trace_start(
    shell_context: "AgentShellContext",
    *,
    prompt_context: "PromptContext",
    prompt_bundle: "PromptBundle",
    user_text: str,
    card_trace_rows: Iterable[Mapping[str, Any]],
) -> PromptTraceEvent | None:
    """记录本轮 Prompt 编译轨迹。失败不阻断主流程。"""
    try:
        event = build_prompt_trace_event(
            session_id=str(getattr(getattr(shell_context, "session", None), "session_id", "")),
            prompt_context=prompt_context,
            prompt_bundle=prompt_bundle,
            user_text=user_text,
            card_trace_rows=card_trace_rows,
        )
        setattr(shell_context, "last_prompt_trace_event", event)
        _append_to_buffer(shell_context, event.public_dict())
        _append_jsonl(shell_context, event.public_dict())
        return event
    except Exception:
        return None


def record_prompt_trace_outcome(
    shell_context: "AgentShellContext",
    *,
    assistant_text: str = "",
    model_ok: bool = False,
    error_summary: str = "",
    provider_not_configured: bool = False,
    plan_failed: bool = False,
) -> dict[str, Any] | None:
    """追加本轮 PromptTrace 的 outcome 与器官卡信用归因。"""
    try:
        event = getattr(shell_context, "last_prompt_trace_event", None)
        if event is None:
            return None
        outcome = build_prompt_trace_outcome(
            event,
            assistant_text=assistant_text,
            model_ok=model_ok,
            error_summary=error_summary,
            provider_not_configured=provider_not_configured,
            plan_failed=plan_failed,
        )
        _append_to_buffer(shell_context, outcome)
        _append_jsonl(shell_context, outcome)
        setattr(shell_context, "last_prompt_trace_outcome", outcome)
        try:
            from .homeostasis_prompt_tuner import update_prompt_tuning_from_outcome

            updated_state = update_prompt_tuning_from_outcome(shell_context, outcome)
            setattr(shell_context, "last_prompt_tuning_state", updated_state)
        except Exception:
            pass
        return outcome
    except Exception:
        return None


def build_prompt_trace_outcome(
    event: PromptTraceEvent,
    *,
    assistant_text: str = "",
    model_ok: bool = False,
    error_summary: str = "",
    provider_not_configured: bool = False,
    plan_failed: bool = False,
) -> dict[str, Any]:
    """从模型输出构造反馈归因记录。"""
    clean_text = _safe_text(assistant_text, 3200)
    clean_error = _safe_text(error_summary, 600)
    planner_leak = _has_any(clean_text, _LEAK_MARKERS)
    internal_log_leak = _has_any(clean_text, _INTERNAL_LOG_MARKERS)
    empty_answer = not bool(clean_text.strip())
    success_proxy = bool(model_ok and not provider_not_configured and not empty_answer and not planner_leak and not internal_log_leak)
    selected_entropy, selected_max_ratio = _selection_diversity(event.selected_organ_counts)
    baseline_shadow_success = _baseline_shadow_success(
        success_proxy=success_proxy,
        model_ok=model_ok,
        provider_not_configured=provider_not_configured,
        empty_answer=empty_answer,
        planner_leak=planner_leak,
        internal_log_leak=internal_log_leak,
        selected_entropy=selected_entropy,
        selected_max_ratio=selected_max_ratio,
    )
    attribution = _attribute_selected_cards(
        event.card_trace_rows,
        success_proxy=success_proxy,
        planner_leak=planner_leak,
        internal_log_leak=internal_log_leak,
        provider_not_configured=provider_not_configured,
        model_ok=model_ok,
    )
    return {
        "schema": L6_72_14_PROMPT_OUTCOME_SCHEMA,
        "trace_id": event.trace_id,
        "timestamp": _utc_now(),
        "session_id": event.session_id,
        "task_mode": event.task_mode,
        "entry_channel": event.entry_channel,
        "provider_ready": event.provider_ready,
        "model_ok": bool(model_ok),
        "provider_not_configured": bool(provider_not_configured),
        "plan_failed_fallback": bool(plan_failed),
        "assistant_digest": _digest_text(clean_text),
        "assistant_chars": len(clean_text),
        "empty_answer": empty_answer,
        "planner_leak_detected": planner_leak,
        "internal_log_leak_detected": internal_log_leak,
        "error_summary": clean_error,
        "success_proxy": success_proxy,
        "baseline_shadow_success_proxy": baseline_shadow_success,
        "selected_organ_counts": dict(event.selected_organ_counts),
        "selected_organ_entropy": round(selected_entropy, 6),
        "selected_max_organ_ratio": round(selected_max_ratio, 6),
        "selected_card_ids": list(event.selected_card_ids),
        "rejected_card_ids": list(event.rejected_card_ids),
        "credit_by_card": attribution["credit_by_card"],
        "credit_by_organ": attribution["credit_by_organ"],
        "feedback_summary": _feedback_summary(
            success_proxy=success_proxy,
            planner_leak=planner_leak,
            internal_log_leak=internal_log_leak,
            provider_not_configured=provider_not_configured,
            model_ok=model_ok,
            empty_answer=empty_answer,
        ),
    }


def recent_prompt_trace_summary(shell_context: "AgentShellContext", *, limit: int = 5) -> list[dict[str, Any]]:
    """返回进程内最近 PromptTrace 记录摘要；不读取外部文件。"""
    buffer = getattr(shell_context, "prompt_trace_buffer", []) or []
    return list(buffer)[-max(1, int(limit)) :]



def _selection_diversity(counts: Mapping[str, int]) -> tuple[float, float]:
    total = sum(max(0, int(value)) for value in counts.values())
    if total <= 0:
        return 1.0, 0.0
    positive = [max(0, int(value)) for value in counts.values() if int(value) > 0]
    if len(positive) <= 1:
        return 0.0, 1.0
    entropy = 0.0
    for count in positive:
        p = count / total
        entropy -= p * math.log(p)
    normalized = entropy / math.log(len(positive)) if len(positive) > 1 else 0.0
    return max(0.0, min(1.0, normalized)), max(0.0, min(1.0, max(positive) / total))


def _baseline_shadow_success(
    *,
    success_proxy: bool,
    model_ok: bool,
    provider_not_configured: bool,
    empty_answer: bool,
    planner_leak: bool,
    internal_log_leak: bool,
    selected_entropy: float,
    selected_max_ratio: float,
) -> bool:
    """保守影子基线。

    没有真实 A/B 时默认不声称 tuner 优于 baseline；只有当输出失败且选择明显
    单器官锁死时，影子基线按“未调权可能避免该锁死”记为候选成功。该值只用于
    调权保护，不进入用户回复。
    """
    if success_proxy:
        return True
    basic_ok = bool(model_ok and not provider_not_configured and not empty_answer and not planner_leak and not internal_log_leak)
    if basic_ok:
        return True
    if bool(model_ok and not provider_not_configured and not empty_answer and selected_entropy < 0.42 and selected_max_ratio > 0.70):
        return True
    return False

def _attribute_selected_cards(
    rows: Iterable[Mapping[str, Any]],
    *,
    success_proxy: bool,
    planner_leak: bool,
    internal_log_leak: bool,
    provider_not_configured: bool,
    model_ok: bool,
) -> dict[str, dict[str, float]]:
    credit_by_card: dict[str, float] = {}
    credit_by_organ: Counter[str] = Counter()
    for row in rows:
        card = row.get("card", {}) if isinstance(row.get("card"), Mapping) else {}
        score = row.get("score", {}) if isinstance(row.get("score"), Mapping) else {}
        if not bool(score.get("selected")):
            continue
        card_id = str(card.get("card_id") or "")
        organ = str(card.get("organ_type") or "unknown")
        credit = 1.0 if success_proxy else -0.45
        if not model_ok:
            credit -= 0.20
        if provider_not_configured and organ == "provider":
            credit -= 0.35
        if planner_leak:
            credit -= 0.35
            if organ == "planner":
                credit -= 0.65
        if internal_log_leak:
            credit -= 0.35
            if organ in {"audit", "runtime", "planner"}:
                credit -= 0.35
        credit = round(max(-1.0, min(1.0, credit)), 4)
        credit_by_card[card_id] = credit
        credit_by_organ[organ] += credit
    return {
        "credit_by_card": credit_by_card,
        "credit_by_organ": {key: round(value, 4) for key, value in credit_by_organ.items()},
    }


def _feedback_summary(
    *,
    success_proxy: bool,
    planner_leak: bool,
    internal_log_leak: bool,
    provider_not_configured: bool,
    model_ok: bool,
    empty_answer: bool,
) -> str:
    if success_proxy:
        return "本轮 PromptBundle 形成有效回复，入选卡获得正向信用。"
    reasons: list[str] = []
    if provider_not_configured:
        reasons.append("provider_not_configured")
    if not model_ok:
        reasons.append("model_not_ok")
    if empty_answer:
        reasons.append("empty_answer")
    if planner_leak:
        reasons.append("planner_or_runtime_log_leak")
    if internal_log_leak:
        reasons.append("internal_log_leak")
    return "本轮 PromptBundle 未计为成功；原因=" + ",".join(reasons or ["unknown"])


def _sanitize_trace_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    clean_rows: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        card = row.get("card", {}) if isinstance(row.get("card"), Mapping) else {}
        score = row.get("score", {}) if isinstance(row.get("score"), Mapping) else {}
        clean_card = {
            "card_id": _safe_text(card.get("card_id", ""), 40),
            "organ_type": _safe_text(card.get("organ_type", "unknown"), 40),
            "source": _safe_text(card.get("source", "unknown"), 120),
            "summary": _safe_text(card.get("summary", ""), 360),
            "authority_level": _safe_text(card.get("authority_level", "organ"), 40),
            "visibility": _safe_text(card.get("visibility", "llm_context"), 40),
            "metadata": _sanitize_mapping(card.get("metadata", {}) if isinstance(card.get("metadata", {}), Mapping) else {}),
        }
        clean_score = {
            "value": _safe_float(score.get("value", 0.0)),
            "selected": bool(score.get("selected")),
            "reason": _safe_text(score.get("reason", ""), 80),
            "task_relevance": _safe_float(score.get("task_relevance", 0.0)),
            "authority": _safe_float(score.get("authority", 0.0)),
            "confidence": _safe_float(score.get("confidence", 0.0)),
            "token_cost": _safe_float(score.get("token_cost", 0.0)),
            "conflict": _safe_float(score.get("conflict", 0.0)),
            "noise": _safe_float(score.get("noise", 0.0)),
            "risk_mismatch": _safe_float(score.get("risk_mismatch", 0.0)),
            "tuning_bias": _safe_float(score.get("tuning_bias", 0.0)),
        }
        clean_rows.append({"card": clean_card, "score": clean_score})
    return clean_rows


def _append_to_buffer(shell_context: "AgentShellContext", record: Mapping[str, Any]) -> None:
    buffer = getattr(shell_context, "prompt_trace_buffer", None)
    if not isinstance(buffer, list):
        buffer = []
        setattr(shell_context, "prompt_trace_buffer", buffer)
    buffer.append(dict(record))
    if len(buffer) > 80:
        del buffer[:-80]


def _append_jsonl(shell_context: "AgentShellContext", record: Mapping[str, Any]) -> None:
    if str(os.getenv("TIANGONG_PROMPT_TRACE_DISABLED", "")).strip().lower() in {"1", "true", "yes", "on"}:
        return
    path = _trace_file_path(shell_context)
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    except Exception:
        return


def _trace_file_path(shell_context: "AgentShellContext") -> Path | None:
    env_path = os.getenv("TIANGONG_PROMPT_TRACE_FILE", "").strip()
    if env_path:
        return Path(env_path).expanduser().resolve()
    workspace = getattr(shell_context, "workspace", None)
    if workspace is None:
        return None
    try:
        root = Path(workspace).expanduser().resolve()
        return root / ".linyuanzhe" / "prompt_trace" / "prompt_trace.jsonl"
    except Exception:
        return None


def _sanitize_mapping(mapping: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in mapping.items():
        key_text = _safe_text(key, 80)
        if isinstance(value, Mapping):
            result[key_text] = _sanitize_mapping(value)
        elif isinstance(value, (int, float, bool)) or value is None:
            result[key_text] = value
        else:
            result[key_text] = _safe_text(value, 240)
    return result


def _safe_text(value: Any, limit: int) -> str:
    text = str(value or "").replace("\x00", " ").replace("\r", " ").strip()
    text = " ".join(part.strip() for part in text.splitlines() if part.strip())
    text = redact_text(text)
    return text[: max(16, int(limit))]


def _digest_text(value: Any) -> str:
    text = _safe_text(value, 4096)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _safe_id(value: Any) -> str:
    return _safe_text(value, 80) or "unknown_session"


def _safe_float(value: Any) -> float:
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return 0.0


def _has_any(text: str, markers: Iterable[str]) -> bool:
    return any(marker and marker in text for marker in markers)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
