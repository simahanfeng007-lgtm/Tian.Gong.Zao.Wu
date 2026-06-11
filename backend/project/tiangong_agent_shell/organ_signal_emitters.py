"""L6.72.16 Organ emit_card 接线层 + PromptTrace + 稳态调权接入。

本模块把 shell/runtime 已有快照转换为 OrganSignalCard，供 PromptCompiler
每轮动态注入。它只读状态、不执行工具、不写记忆、不改 Runtime 主链。

设计边界：
- 器官接线只 emit_card，不拼 system prompt。
- 只读取已有 public/snapshot 接口，失败则降级为 trace，不阻断聊天。
- 普通聊天可注入 UI/Provider/Runtime/Memory/Emotion 等轻卡，但 PlannerCard
  仍由 AttentionGate 在 ordinary_chat 下硬阻断。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable, Mapping, TYPE_CHECKING

from .organ_signal_card import OrganSignalCard, emit_organ_signal_card

if TYPE_CHECKING:  # pragma: no cover - only for type checkers
    from .composition_root import AgentShellContext


L6_72_13_ORGAN_EMITTER_SCHEMA = "tiangong.l6_72_13.organ_emit_card_wiring.v1"
L6_72_14_PROMPT_TRACE_WIRING = "tiangong.l6_72_14.prompt_trace_wiring.v1"


_ALLOWED_TASK_MODES = {"ordinary_chat", "tool_task", "code_task", "file_task", "diagnostic_task"}


def collect_organ_signal_cards(
    context: "AgentShellContext",
    *,
    user_text: str = "",
    task_mode: str = "ordinary_chat",
) -> tuple[OrganSignalCard, ...]:
    """收集当前 shell/runtime 可安全上报的器官信号卡。

    这是 L6.72.13 的唯一接线入口。调用方将这些卡传入 PromptCompiler，
    而不是让 Runtime/Memory/Skill/Emotion 等模块各自拼 prompt。
    """
    task = _normalize_task(task_mode)
    cards: list[OrganSignalCard] = []
    for emitter in (
        emit_ui_state_card,
        emit_provider_state_card,
        emit_runtime_state_card,
        emit_tool_state_card,
        emit_risk_state_card,
        emit_memory_recall_card,
        emit_skill_state_card,
        emit_emotion_state_card,
        emit_self_heal_state_card,
        emit_lifecycle_state_card,
        emit_planner_state_card,
        emit_audit_state_card,
    ):
        try:
            cards.extend(emitter(context, user_text=user_text, task_mode=task))
        except Exception as exc:  # noqa: BLE001 - signal wiring must not break chat
            cards.append(_error_trace_card(emitter.__name__, exc))
    return tuple(cards)


def refresh_session_system_prompt(
    context: "AgentShellContext",
    *,
    user_text: str = "",
    task_mode: str = "ordinary_chat",
) -> tuple[OrganSignalCard, ...]:
    """收集器官卡、刷新 system prompt，并写入 PromptTrace 起点。

    只更新 system 消息，不改用户/assistant 历史，不触发模型或工具；PromptTrace
    只进入内部 JSONL/进程缓冲，不进入 LLM prompt 与用户回复。
    """
    from .prompt_compiler import build_prompt_context, compile_prompt, trace_prompt_organ_signals
    from .prompt_trace import record_prompt_trace_start
    from .homeostasis_prompt_tuner import get_prompt_tuning_state

    task = _normalize_task(task_mode)
    cards = collect_organ_signal_cards(context, user_text=user_text, task_mode=task)
    prompt_tuning_state = get_prompt_tuning_state(context).public_dict()
    prompt_context = build_prompt_context(
        context.config,
        task_mode=task,
        organ_signal_cards=cards,
        prompt_tuning_state=prompt_tuning_state,
    )
    prompt_bundle = compile_prompt(prompt_context)
    setter = getattr(context.session, "set_system_prompt", None)
    if callable(setter):
        setter(prompt_bundle.system_prompt)
    else:  # 兼容旧 SessionState
        dialog = [message for message in context.session.messages if message.get("role") != "system"]
        context.session.messages = [{"role": "system", "content": prompt_bundle.system_prompt}] + dialog
    record_prompt_trace_start(
        context,
        prompt_context=prompt_context,
        prompt_bundle=prompt_bundle,
        user_text=user_text,
        card_trace_rows=trace_prompt_organ_signals(prompt_context),
    )
    return cards


def emit_ui_state_card(context: "AgentShellContext", *, user_text: str = "", task_mode: str = "ordinary_chat") -> tuple[OrganSignalCard, ...]:
    entry = os.getenv("TIANGONG_ENTRY_CHANNEL") or ("desktop_gui" if os.getenv("TIANGONG_CONVERSATION_FILE") else "cli")
    conv = os.getenv("TIANGONG_CONVERSATION_FILE", "")
    summary = (
        f"入口={entry}；session_id={_safe(getattr(context.session, 'session_id', ''), 64)}；"
        f"message_count={getattr(context.session, 'message_count', len(getattr(context.session, 'messages', [])))}；"
        f"conversation_file={'已启用' if conv else '未启用'}。"
    )
    return (
        emit_organ_signal_card(
            organ_type="ui",
            summary=summary,
            source="shell.ui_state",
            authority_level="system",
            task_relevance=0.78 if entry == "desktop_gui" else 0.58,
            confidence=0.86,
            utility_history=0.70,
            ttl_seconds=900.0,
            metadata={"schema": L6_72_13_ORGAN_EMITTER_SCHEMA, "task_mode": task_mode},
        ),
    )


def emit_provider_state_card(context: "AgentShellContext", *, user_text: str = "", task_mode: str = "ordinary_chat") -> tuple[OrganSignalCard, ...]:
    cfg = context.config
    ready = bool(getattr(cfg, "has_real_api_key", False) and getattr(cfg, "base_url", "") and getattr(cfg, "model", "") and getattr(cfg, "provider", "") != "mock")
    summary = (
        f"Provider={_safe(getattr(cfg, 'provider', ''), 40)}；model={_safe(getattr(cfg, 'model', '') or '未设置', 80)}；"
        f"base_url_configured={bool(getattr(cfg, 'base_url', ''))}；key_ready={bool(getattr(cfg, 'has_real_api_key', False))}；"
        f"real_model_ready={ready}。未配置时不得 Mock 回复。"
    )
    return (
        emit_organ_signal_card(
            organ_type="provider",
            summary=summary,
            source="shell.provider_state",
            authority_level="system",
            task_relevance=0.74,
            confidence=0.90,
            utility_history=0.74,
            risk_score=0.10 if ready else 0.38,
            ttl_seconds=600.0,
            metadata={"schema": L6_72_13_ORGAN_EMITTER_SCHEMA},
        ),
    )


def emit_runtime_state_card(context: "AgentShellContext", *, user_text: str = "", task_mode: str = "ordinary_chat") -> tuple[OrganSignalCard, ...]:
    runtime = context.runtime
    pending = _safe_len(_call(runtime, "pending_confirmations", default=[]))
    reports = _collect_snapshot_statuses(
        runtime,
        (
            "planner_execution_snapshot",
            "quality_gate_snapshot",
            "delivery_snapshot",
            "project_snapshot",
            "interface_wiring_snapshot",
        ),
        limit=5,
    )
    summary = (
        f"Runtime=已装配；workspace={_short_path(context.workspace)}；max_steps={context.max_steps}；"
        f"pending_confirmations={pending}；kernel_importable={context.kernel_importable}；"
        f"近期状态={'; '.join(reports) if reports else '暂无执行报告'}。"
    )
    return (
        emit_organ_signal_card(
            organ_type="runtime",
            summary=summary,
            source="runtime.snapshot_bus",
            authority_level="runtime",
            task_relevance=0.64 if task_mode == "ordinary_chat" else 0.88,
            confidence=0.86,
            utility_history=0.78,
            homeostasis_need=0.42 if pending else 0.18,
            risk_score=0.20 if pending else 0.06,
            ttl_seconds=600.0,
            metadata={"schema": L6_72_13_ORGAN_EMITTER_SCHEMA, "pending_confirmations": pending},
        ),
    )


def emit_tool_state_card(context: "AgentShellContext", *, user_text: str = "", task_mode: str = "ordinary_chat") -> tuple[OrganSignalCard, ...]:
    tools = _call(context.runtime, "available_tools", default=[])
    names: list[str] = []
    risks: list[str] = []
    for tool in list(tools or [])[:8]:
        names.append(_safe(getattr(tool, "name", "tool"), 48))
        risks.append(_safe(getattr(tool, "default_risk", "A?"), 8))
    mode = getattr(getattr(context.config, "tool_execution_mode", ""), "value", str(getattr(context.config, "tool_execution_mode", "")))
    summary = (
        f"工具模式={mode}；available_tool_count={len(tools or [])}；"
        f"top_tools={', '.join(names) if names else '无'}；risk_samples={', '.join(risks) if risks else '无'}。"
    )
    return (
        emit_organ_signal_card(
            organ_type="tool",
            summary=summary,
            source="runtime.tool_registry",
            authority_level="runtime",
            task_relevance=0.18 if task_mode == "ordinary_chat" else 0.86,
            confidence=0.82,
            utility_history=0.72,
            homeostasis_need=0.30 if task_mode != "ordinary_chat" else 0.04,
            ttl_seconds=600.0,
            metadata={"schema": L6_72_13_ORGAN_EMITTER_SCHEMA, "tool_count": len(tools or [])},
        ),
    )


def emit_risk_state_card(context: "AgentShellContext", *, user_text: str = "", task_mode: str = "ordinary_chat") -> tuple[OrganSignalCard, ...]:
    pending = _safe_len(_call(context.runtime, "pending_confirmations", default=[]))
    summary = "A5 极高危硬拦；A0-A4 由 Runtime 管控、确认和审计；器官卡不得授权、拒绝或绕过 Runtime。"
    if pending:
        summary += f"当前存在待确认票据 {pending} 个，必须维持确认链。"
    return (
        emit_organ_signal_card(
            organ_type="risk",
            summary=summary,
            source="runtime.risk_policy",
            authority_level="runtime",
            task_relevance=0.78 if task_mode == "ordinary_chat" else 0.90,
            confidence=0.92,
            urgency=0.34 if pending else 0.10,
            utility_history=0.82,
            risk_score=0.18 if pending else 0.06,
            ttl_seconds=1800.0,
            metadata={"schema": L6_72_13_ORGAN_EMITTER_SCHEMA, "pending_confirmations": pending},
        ),
    )


def emit_memory_recall_card(context: "AgentShellContext", *, user_text: str = "", task_mode: str = "ordinary_chat") -> tuple[OrganSignalCard, ...]:
    snap = _call(context.runtime, "memory_recall_runtime_snapshot", default={})
    if not isinstance(snap, Mapping):
        return tuple()
    route = snap.get("route") if isinstance(snap.get("route"), Mapping) else None
    if not route:
        attached = bool(snap.get("memory_store_attached"))
        err = _safe(snap.get("last_error", ""), 160)
        if not attached and not err:
            return tuple()
        summary = f"MemoryRecall 快照：store_attached={attached}；last_error={err or '无'}；summary_only=True；no_raw_memory_body=True。"
    else:
        hints = route.get("hints") if isinstance(route.get("hints"), list) else []
        hint_text = _summarize_list(hints, keys=("summary", "hint", "text", "sanitized_summary"), limit=3, max_chars=520)
        filtered = route.get("filtered_count", 0)
        summary = f"MemoryRecall 只读摘要：hints={len(hints)}；filtered={filtered}；{hint_text or '无可注入摘要'}。"
    return (
        emit_organ_signal_card(
            organ_type="memory",
            summary=summary,
            source="runtime.memory_recall_snapshot",
            authority_level="organ",
            task_relevance=0.68,
            confidence=0.66,
            utility_history=0.62,
            token_cost=None,
            ttl_seconds=900.0,
            metadata={"schema": L6_72_13_ORGAN_EMITTER_SCHEMA, "summary_only": True},
        ),
    )


def emit_skill_state_card(context: "AgentShellContext", *, user_text: str = "", task_mode: str = "ordinary_chat") -> tuple[OrganSignalCard, ...]:
    runtime = context.runtime
    statuses = _collect_snapshot_statuses(
        runtime,
        (
            "skill_queue_snapshot",
            "learning_convergence_snapshot",
            "exoskeleton_snapshot",
            "tool_request_snapshot",
            "learning_asset_activation_status",
        ),
        limit=6,
    )
    activation = _call(runtime, "learning_asset_activation_status", default={})
    act_summary = ""
    if isinstance(activation, Mapping):
        act_summary = _safe(activation.get("summary") or activation.get("status") or "", 180)
    if not statuses and not act_summary:
        return tuple()
    summary = f"Skill/Ability 执行神经回路快照：{'; '.join(statuses) if statuses else '暂无队列状态'}。{act_summary}"
    return (
        emit_organ_signal_card(
            organ_type="skill",
            summary=summary,
            source="runtime.skill_ability_snapshots",
            authority_level="organ",
            task_relevance=0.34 if task_mode == "ordinary_chat" else 0.84,
            confidence=0.72,
            utility_history=0.74,
            ttl_seconds=1200.0,
            metadata={"schema": L6_72_13_ORGAN_EMITTER_SCHEMA},
        ),
    )


def emit_emotion_state_card(context: "AgentShellContext", *, user_text: str = "", task_mode: str = "ordinary_chat") -> tuple[OrganSignalCard, ...]:
    snap = _call(context.runtime, "affective_runtime_snapshot", default={})
    summary = ""
    if isinstance(snap, Mapping) and snap.get("has_previous_state"):
        route = snap.get("route") if isinstance(snap.get("route"), Mapping) else {}
        state = snap.get("state") if isinstance(snap.get("state"), Mapping) else {}
        dominant = _deep_get(state, ("dominant_emotion",)) or _deep_get(route, ("dominant_emotion",)) or "unknown"
        hint = _deep_get(route, ("planner_hint", "style_hint")) or _deep_get(route, ("planner_hint", "summary")) or ""
        summary = f"情感总色彩只读投影：dominant={_safe(dominant, 40)}；style_hint={_safe(hint, 220)}；只影响表达底色和行为偏置，不覆盖用户目标。"
    else:
        env_style = os.getenv("TIANGONG_AFFECTIVE_STYLE_HINT") or os.getenv("TIANGONG_EMOTION_STYLE_HINT") or ""
        if env_style:
            summary = f"情感风格环境提示：{_safe(env_style, 260)}；不得覆盖 Kernel 和用户目标。"
    if not summary:
        return tuple()
    return (
        emit_organ_signal_card(
            organ_type="emotion",
            summary=summary,
            source="runtime.affective_snapshot",
            authority_level="organ",
            task_relevance=0.54 if task_mode == "ordinary_chat" else 0.26,
            confidence=0.62,
            utility_history=0.52,
            noise_score=0.06,
            ttl_seconds=900.0,
            metadata={"schema": L6_72_13_ORGAN_EMITTER_SCHEMA, "no_authorization": True},
        ),
    )


def emit_self_heal_state_card(context: "AgentShellContext", *, user_text: str = "", task_mode: str = "ordinary_chat") -> tuple[OrganSignalCard, ...]:
    runtime = context.runtime
    statuses = _collect_snapshot_statuses(
        runtime,
        (
            "recovery_coordination_snapshot",
            "project_repair_snapshot",
            "quality_gate_snapshot",
            "diagnosis_snapshot",
            "execution_chain_freeze_snapshot",
        ),
        limit=5,
    )
    if not statuses and task_mode != "diagnostic_task":
        return tuple()
    summary = f"自愈/恢复只读信号：{'; '.join(statuses) if statuses else '暂无最近诊断'}；只能建议复检、回滚或恢复路径，不得直接应用补丁。"
    return (
        emit_organ_signal_card(
            organ_type="self_heal",
            summary=summary,
            source="runtime.self_heal_snapshots",
            authority_level="organ",
            task_relevance=0.20 if task_mode == "ordinary_chat" else 0.82,
            confidence=0.70,
            utility_history=0.68,
            homeostasis_need=0.46 if task_mode == "diagnostic_task" else 0.18,
            ttl_seconds=900.0,
            metadata={"schema": L6_72_13_ORGAN_EMITTER_SCHEMA, "no_patch_apply": True},
        ),
    )


def emit_lifecycle_state_card(context: "AgentShellContext", *, user_text: str = "", task_mode: str = "ordinary_chat") -> tuple[OrganSignalCard, ...]:
    snap = _call(context.runtime, "lifecycle_runtime_snapshot", default={})
    if not isinstance(snap, Mapping):
        return tuple()
    bundle = snap.get("bundle") if isinstance(snap.get("bundle"), Mapping) else None
    if bundle:
        status = _deep_get(bundle, ("status_route", "status")) or _deep_get(bundle, ("status_route", "status_summary")) or "active"
        hints = _summarize_list(bundle.get("next_action_hints", []), keys=("summary", "action", "reason"), limit=3, max_chars=420)
        summary = f"生命周期协调信号：status={_safe(status, 80)}；hints={hints or '无'}；no_direct_execution=True。"
    else:
        return tuple()
    return (
        emit_organ_signal_card(
            organ_type="lifecycle",
            summary=summary,
            source="runtime.lifecycle_snapshot",
            authority_level="organ",
            task_relevance=0.18 if task_mode == "ordinary_chat" else 0.38,
            confidence=0.64,
            utility_history=0.55,
            ttl_seconds=1200.0,
            metadata={"schema": L6_72_13_ORGAN_EMITTER_SCHEMA, "no_direct_execution": True},
        ),
    )


def emit_planner_state_card(context: "AgentShellContext", *, user_text: str = "", task_mode: str = "ordinary_chat") -> tuple[OrganSignalCard, ...]:
    mode = getattr(getattr(context.config, "planner_mode", ""), "value", str(getattr(context.config, "planner_mode", "")))
    snap = _call(context.runtime, "planner_context_snapshot", default={})
    status = _safe(snap.get("status", "empty") if isinstance(snap, Mapping) else "empty", 80)
    summary = f"Planner 是小脑建议器：planner_mode={mode}；planner_context_status={status}；普通聊天不得进入 Planner 执行链。"
    return (
        emit_organ_signal_card(
            organ_type="planner",
            summary=summary,
            source="runtime.planner_snapshot",
            authority_level="organ",
            task_relevance=0.20 if task_mode == "ordinary_chat" else 0.70,
            confidence=0.72,
            utility_history=0.60,
            noise_score=0.12 if task_mode == "ordinary_chat" else 0.04,
            ttl_seconds=600.0,
            metadata={"schema": L6_72_13_ORGAN_EMITTER_SCHEMA, "ordinary_chat_must_block": task_mode == "ordinary_chat"},
        ),
    )


def emit_audit_state_card(context: "AgentShellContext", *, user_text: str = "", task_mode: str = "ordinary_chat") -> tuple[OrganSignalCard, ...]:
    audit = getattr(context.runtime, "audit", None)
    events = _call(audit, "recent_summary", default=[]) if audit is not None else []
    if not events:
        return tuple()
    summary = f"审计只读摘要：recent_events={len(events)}；仅用于诊断/追踪，不进入用户回复。"
    visibility = "llm_context" if task_mode == "diagnostic_task" else "trace_only"
    return (
        emit_organ_signal_card(
            organ_type="audit",
            summary=summary,
            source="runtime.audit_summary",
            authority_level="runtime",
            task_relevance=0.20 if task_mode != "diagnostic_task" else 0.82,
            confidence=0.78,
            utility_history=0.62,
            visibility=visibility,
            ttl_seconds=600.0,
            metadata={"schema": L6_72_13_ORGAN_EMITTER_SCHEMA, "trace_only_unless_diagnostic": True},
        ),
    )


def _error_trace_card(source: str, exc: Exception) -> OrganSignalCard:
    return emit_organ_signal_card(
        organ_type="audit",
        summary=f"器官信号接线失败：{_safe(source, 80)} -> {type(exc).__name__}: {_safe(exc, 160)}。该失败只进 trace，不阻断用户回复。",
        source="organ_signal_emitters.error",
        authority_level="system",
        task_relevance=0.10,
        confidence=0.40,
        noise_score=0.30,
        visibility="trace_only",
        ttl_seconds=300.0,
        metadata={"schema": L6_72_13_ORGAN_EMITTER_SCHEMA},
    )


def _collect_snapshot_statuses(runtime: Any, method_names: Iterable[str], *, limit: int = 6) -> list[str]:
    statuses: list[str] = []
    for name in method_names:
        payload = _call(runtime, name, default=None)
        if not isinstance(payload, Mapping):
            continue
        label = name.replace("_snapshot", "").replace("_", ":")
        status = payload.get("status") or payload.get("decision") or payload.get("message")
        if status is None and isinstance(payload.get("report"), Mapping):
            status = payload["report"].get("status") or payload["report"].get("summary")
        if status is None and isinstance(payload.get("bundle"), Mapping):
            status = payload["bundle"].get("status") or "bundle_ready"
        if status is None:
            continue
        text = _safe(status, 96)
        if text and text.lower() not in {"empty", "none", "null"}:
            statuses.append(f"{label}={text}")
        if len(statuses) >= limit:
            break
    return statuses


def _summarize_list(items: Any, *, keys: tuple[str, ...], limit: int, max_chars: int) -> str:
    if not isinstance(items, list):
        return ""
    parts: list[str] = []
    for item in items[: max(0, int(limit))]:
        if isinstance(item, Mapping):
            text = ""
            for key in keys:
                value = item.get(key)
                if value:
                    text = _safe(value, max_chars)
                    break
            if not text:
                text = _safe(item, max_chars)
        else:
            text = _safe(item, max_chars)
        if text:
            parts.append(text)
    return " | ".join(parts)[: max(80, int(max_chars))]


def _deep_get(payload: Any, path: tuple[str, ...]) -> Any:
    cur = payload
    for key in path:
        if not isinstance(cur, Mapping):
            return None
        cur = cur.get(key)
    return cur


def _call(target: Any, name: str, *, default: Any) -> Any:
    fn = getattr(target, name, None)
    if not callable(fn):
        return default
    try:
        return fn()
    except Exception:
        return default


def _safe_len(value: Any) -> int:
    try:
        return len(value or [])
    except TypeError:
        return 0


def _short_path(value: Any) -> str:
    try:
        path = Path(value)
        return _safe(path.name or str(path), 80)
    except Exception:
        return _safe(value, 80)


def _safe(value: Any, limit: int) -> str:
    text = str(value or "").replace("\x00", " ").replace("\r", " ").strip()
    text = " ".join(part.strip() for part in text.splitlines() if part.strip())
    lowered = text.lower()
    if any(marker in lowered for marker in ("api_key", "apikey", "authorization", "bearer ", "secret", "password", "credential", "token=")):
        return "[redacted-sensitive-summary]"
    for raw in (os.getenv("TIANGONG_API_KEY", ""), os.getenv("DEEPSEEK_API_KEY", ""), os.getenv("OPENAI_API_KEY", "")):
        if raw:
            text = text.replace(raw, "<redacted>")
    return text[: max(16, int(limit))]


def _normalize_task(value: Any) -> str:
    clean = str(value or "ordinary_chat").strip().lower().replace("-", "_")
    return clean if clean in _ALLOWED_TASK_MODES else "ordinary_chat"
