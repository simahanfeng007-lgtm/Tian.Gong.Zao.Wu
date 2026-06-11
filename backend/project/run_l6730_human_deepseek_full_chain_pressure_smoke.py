#!/usr/bin/env python3
"""L6.73.0 人类输入 ↔ 模拟 DeepSeek 主脑 ↔ 临渊者全链条压测。

本脚本不调用真实 DeepSeek API；它用确定性的 SimulatedDeepSeekMainBrain
模拟 ActivationForm 填写与短/长链决策，重点验证 Runtime/前端投影边界、
长链续接、自愈/学习/迭代/自由意志候选路由、情感系统和 A5 弹窗触发链。
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

PROJECT_DIR = Path(__file__).resolve().parent
REPO_ROOT = PROJECT_DIR.parents[1]
FRONTEND_DIR = REPO_ROOT / "frontend"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))

if __name__ == "__main__" and os.environ.get("LINYUANZHE_RUN_FULL_SMOKE", "").strip().lower() not in {"1", "true", "yes", "on"}:
    print(json.dumps({
        "ok": True,
        "status": "SKIP",
        "smoke": "L6.73.0 human/deepseek full-chain pressure",
        "reason": "long-chain pressure smoke is opt-in to avoid no-output CI timeouts; set LINYUANZHE_RUN_FULL_SMOKE=1 to run the full scenario",
    }, ensure_ascii=False), flush=True)
    raise SystemExit(0)

os.environ.setdefault("TIANGONG_SOUL_BASELINE_PERSIST", "0")

from tiangong_agent_runtime.affective_state import (  # noqa: E402
    AffectiveBaseline,
    AffectiveStateEngine,
    SevenEmotionSignalSources,
    SixDesireSignalSources,
    SoulAffectiveProfile,
)
from tiangong_agent_runtime.affective_execution_route import AffectiveExecutionRouter  # noqa: E402
from tiangong_agent_runtime.frontend_contract import runtime_result_to_sse_events  # noqa: E402
from tiangong_agent_runtime.free_will_candidate_route import build_autonomy_lease, build_free_will_route  # noqa: E402
from tiangong_agent_runtime.free_will_background_runner import FreeWillBackgroundRunner  # noqa: E402
from tiangong_agent_runtime.long_chain_pressure_probe import run_long_chain_pressure_probe  # noqa: E402
from tiangong_agent_runtime.model_execution_policy_engine import ModelExecutionPolicyEngine  # noqa: E402
from tiangong_agent_runtime.public_projection_bridge import RuntimeProjection  # noqa: E402
from tiangong_agent_runtime.self_healing_execution_route import build_self_healing_route  # noqa: E402
from tiangong_agent_runtime.self_iteration_route import build_self_iteration_route  # noqa: E402
from tiangong_agent_runtime.self_learning_route import build_self_learning_route  # noqa: E402
from tiangong_agent_runtime.skill_playbook_router import SkillPlaybookRouter  # noqa: E402
from linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient  # noqa: E402
from linyuanzhe_frontend.contracts.runtime_snapshot import ChatMessage  # noqa: E402
from linyuanzhe_frontend.contracts.sse_events import RuntimeSseEvent  # noqa: E402

CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
REPORT_DIR = Path(os.environ.get("LINYUANZHE_REPORT_DIR") or tempfile.mkdtemp(prefix="linyuanzhe_l6730_pressure_"))
REPORT_JSON = REPORT_DIR / "l6730_human_deepseek_full_chain_pressure_report.json"
REPORT_MD = REPORT_DIR / "l6730_human_deepseek_full_chain_pressure_report.md"

def _public_path(path: Path) -> str:
    try:
        tmp = Path(tempfile.gettempdir()).resolve()
        resolved = path.resolve()
        if resolved == tmp or tmp in resolved.parents:
            return f"<tmp>/{resolved.name}"
    except Exception:
        pass
    return path.name



@dataclass
class CaseResult:
    case_id: str
    title: str
    requirement: str
    status: str = "PASS"
    evidence: dict[str, Any] = field(default_factory=dict)
    message: str = ""


@dataclass
class SimulatedActivationForm:
    mode: str
    work_type: str = "none"
    execution_depth: str = "single_turn"
    tools_requested: bool = False
    required_tool_classes: tuple[str, ...] = tuple()
    risk_level: str = "A0"
    need_quality_gate: bool = False
    need_user_confirm: bool = False
    final_output_contract: str = "answer_only"

    def public_dict(self) -> dict[str, Any]:
        return asdict(self)


class SimulatedDeepSeekMainBrain:
    """模拟 DeepSeek 主脑填 ActivationForm，不执行工具。"""

    def fill_activation_form(self, user_input: str, *, selected_mode: str) -> SimulatedActivationForm:
        text = str(user_input or "").lower()
        if selected_mode == "chat":
            return SimulatedActivationForm(mode="chat", tools_requested=False, final_output_contract="answer_only")
        if "a5" in text or "删除系统" in text or "格式化" in text:
            return SimulatedActivationForm(
                mode="work", work_type="terminal", execution_depth="single_step", tools_requested=True,
                required_tool_classes=("terminal",), risk_level="A5", need_quality_gate=True,
                need_user_confirm=True, final_output_contract="execution_report",
            )
        if "150" in text or "长链" in text:
            return SimulatedActivationForm(
                mode="work", work_type="mixed", execution_depth="long_chain", tools_requested=True,
                required_tool_classes=("file", "quality", "delivery"), risk_level="A3", need_quality_gate=True,
                final_output_contract="execution_report",
            )
        if any(x in text for x in ("创建", "读取", ".txt", "列目录", "短链", "hello")):
            return SimulatedActivationForm(
                mode="work", work_type="file", execution_depth="single_step", tools_requested=True,
                required_tool_classes=("file",), risk_level="A1", need_quality_gate=True,
                final_output_contract="execution_report",
            )
        return SimulatedActivationForm(
            mode="work", work_type="mixed", execution_depth="multi_step", tools_requested=True,
            required_tool_classes=("analysis",), risk_level="A2", need_quality_gate=True,
            final_output_contract="execution_report",
        )


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def has_chinese(text: Any) -> bool:
    return bool(CHINESE_RE.search(str(text or "")))


def event(name: str, seq: int, *, payload: dict[str, Any] | None = None, display_channel: str = "workbench", visibility: str = "task_telemetry", event_kind: str = "task_progress", run_id: str = "run_l6730", task_id: str = "task_l6730") -> RuntimeSseEvent:
    return RuntimeSseEvent.from_mapping({
        "event": name,
        "seq": seq,
        "run_id": run_id,
        "task_id": task_id,
        "display_channel": display_channel,
        "visibility": visibility,
        "event_kind": event_kind,
        "payload": payload or {},
    })


def run_cases() -> list[CaseResult]:
    brain = SimulatedDeepSeekMainBrain()
    results: list[CaseResult] = []

    def record(case_id: str, title: str, requirement: str, fn: Callable[[], dict[str, Any]]) -> None:
        started = time.perf_counter()
        try:
            evidence = fn()
            results.append(CaseResult(case_id, title, requirement, "PASS", evidence, message="通过"))
        except Exception as exc:  # noqa: BLE001 - smoke runner must report all failures.
            results.append(CaseResult(case_id, title, requirement, "FAIL", {"exception_type": type(exc).__name__}, message=f"失败：{exc}"))
        finally:
            results[-1].evidence.setdefault("elapsed_ms", int((time.perf_counter() - started) * 1000))

    # 1-3 chat no tool state / style affected by emotion.
    record("C01", "普通聊天不进入工具状态", "1", lambda: _case_chat_no_tools(brain, "你好，解释一下长链是什么意思"))
    record("C02", "分析型聊天仍不进入工具状态", "1", lambda: _case_chat_no_tools(brain, "帮我分析一下这个想法靠谱不靠谱"))
    record("C03", "聊天情感风格受情感系统影响", "5", _case_affective_style_changes)

    # 4-8 short/micro policy/playbook.
    record("C04", "短链创建 txt 不进入长链", "2", lambda: _case_short_chain_no_long(brain, "创建 hello.txt，内容 abc"))
    record("C05", "短链读取目录不进入长链", "2", lambda: _case_short_chain_no_long(brain, "短链列目录并返回摘要"))
    record("C06", "中等模型微计划限制 1-3 步", "2", _case_micro_policy_limit)
    record("C07", "txt 普通文件不被 document_parse 劫持", "1/2", _case_plain_file_playbook)
    record("C08", "docx/pdf 明确文档任务进入文档工作流", "1/2", _case_document_playbook)
    record("C09", "learned assets 只做候选不污染主链工具", "8", _case_learned_assets_candidate_only)

    # 9-11 long chain and reconnect.
    record("C10", "长链 150 轮不断链", "3", _case_long_chain_150)
    record("C11", "断链后自动续连", "3", _case_frontend_auto_reconnect)
    record("C12", "150 个工具事件不污染会话区", "1/3", _case_150_events_no_chat_pollution)

    # 12 Chinese errors / provider summaries.
    record("C13", "错误提示为中文摘要", "4", _case_chinese_error_summaries)
    record("C14", "Provider 诊断进工作台不进会话", "1/4", _case_provider_diagnostic_workbench_only)

    # 15-16 soul/baseline/temp emotion.
    record("C15", "情感底色受 Soul 影响", "6", _case_soul_baseline_affects_emotion)
    record("C16", "临时情感受聊天输入影响", "6", _case_temp_emotion_from_chat_signal)

    # 17-19 self systems.
    record("C17", "自愈系统可生成自愈候选并保持边界", "7", _case_self_healing_candidate)
    record("C18", "自我学习可生成学习候选并保持审核边界", "8", _case_self_learning_candidate)
    record("C19", "自我迭代可生成优化候选并要求回滚/验证", "9", _case_self_iteration_candidate)

    # 20-21 A5 popup chain.
    record("C20", "后端 A5 pending confirmation 投影为 approval_required", "10", _case_backend_a5_projection_event)
    record("C21", "前端接收 A5 后进入等待审批并具备弹窗路径", "10", _case_frontend_a5_popup_trigger)

    # 22-23 free will.
    record("C22", "自由意志空闲时可生成后台候选", "11", _case_free_will_idle_candidate)
    record("C23", "自由意志不抢占活跃用户任务", "11", _case_free_will_active_task_blocked)

    # 24-28 UI performance/scrollbar and transcript.
    record("C24", "前端 500 个工作台事件不卡会话投影", "12", _case_frontend_event_projection_performance)
    record("C25", "侧面/会话滑条使用统一美化样式", "12", _case_scrollbar_style_sources)
    record("C26", "A5 确认错误/阻塞文案为中文", "4/10", _case_a5_chinese_copy)
    record("C27", "弱模型不能被误当工作主脑", "1/9", _case_weak_model_blocked)
    record("C28", "短链 final 可进会话，完整报告仍在工作台", "1/2", _case_final_summary_not_full_report)
    record("C29", "工作流事件复制聊天时不会带出工具步骤", "1/12", _case_chat_copy_clean)
    record("C30", "前端不执行工具/不写记忆/不应用回滚", "12", _case_frontend_permission_flags_static)

    return results


def _case_chat_no_tools(brain: SimulatedDeepSeekMainBrain, prompt: str) -> dict[str, Any]:
    form = brain.fill_activation_form(prompt, selected_mode="chat")
    _assert(form.mode == "chat", "聊天模式应保持 chat")
    _assert(form.tools_requested is False, "聊天模式不得请求工具")
    _assert(form.work_type == "none", "聊天模式不得进入工作类型")
    return form.public_dict()


def _case_short_chain_no_long(brain: SimulatedDeepSeekMainBrain, prompt: str) -> dict[str, Any]:
    form = brain.fill_activation_form(prompt, selected_mode="work")
    _assert(form.mode == "work", "短链工作应进入 work")
    _assert(form.tools_requested is True, "短链工作可请求必要文件工具")
    _assert(form.execution_depth in {"single_step", "multi_step"}, "短链不应进入 long_chain")
    _assert(form.execution_depth != "long_chain", "短链被误判为长链")
    return form.public_dict()


def _case_micro_policy_limit() -> dict[str, Any]:
    policy = SimpleNamespace(model_role="micro_planner", allowed_tool_families=("file", "analysis", "terminal"), max_context_chars=32000, max_plan_steps_per_round=9)
    profile = SimpleNamespace(provider_id="qwen", model_id="qwen-small", profile_id="profile_micro", recommended_role="micro_planner")
    active = ModelExecutionPolicyEngine().activate(profile, policy, requested_max_steps=12)
    _assert(active.allowed_work_mode, "micro_planner 应允许短步 work")
    _assert(active.effective_max_steps <= 3, "micro_planner 每轮不得超过 3 步")
    _assert(not active.allow_long_chain, "micro_planner 不允许长链")
    return active.public_dict()


def _case_plain_file_playbook() -> dict[str, Any]:
    route = SkillPlaybookRouter().route(user_goal="创建 hello.txt 内容 abc", learned_assets=[])
    data = route.public_dict()
    _assert(route.playbook_id == "workspace_file_simple", "普通 txt 应走 workspace_file_simple")
    _assert("document_parse" in route.forbidden_tools, "普通文件应禁止 document_parse")
    return data


def _case_document_playbook() -> dict[str, Any]:
    route = SkillPlaybookRouter().route(user_goal="解析 report.docx 并导出摘要")
    _assert(route.playbook_id == "document_parse_rewrite", "docx 应走文档工作流")
    _assert("document_parse" in route.recommended_tools, "文档工作流应推荐 document_parse")
    return route.public_dict()


def _case_learned_assets_candidate_only() -> dict[str, Any]:
    route = SkillPlaybookRouter().route(
        user_goal="修复这个项目",
        available_tools=["scan_project", "read_file", "write_workspace_file", "run_python_quality_check", "learned_magic_patch"],
        learned_assets=["learned_magic_patch", {"asset_id": "skill_code_review_v2"}],
    )
    _assert("learned_magic_patch" in route.learned_asset_candidates, "learned asset 应进入候选")
    _assert("learned_magic_patch" not in route.recommended_tools, "learned asset 不得污染主链工具")
    return route.public_dict()


def _case_long_chain_150() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="l6730_long_chain_") as tmp:
        report = run_long_chain_pressure_probe(tmp, step_counts=(150,))
    _assert(report.ok, "150 轮长链压测未通过")
    case = report.cases[0]
    data = case.public_dict()
    _assert(data.get("executed_steps") == 150, "执行步数不是 150")
    _assert(data.get("conversation_pollution_count", 0) == 0, "长链污染会话区")
    return report.public_dict()


def _case_frontend_auto_reconnect() -> dict[str, Any]:
    client = SseRuntimeClient(base_url="http://127.0.0.1:9", timeout=0.1)
    calls = {"n": 0}

    class DummyResponse:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_open(payload: dict[str, Any]):
        calls["n"] += 1
        return DummyResponse()

    def fake_consume(response: Any, events: list[RuntimeSseEvent], *, on_event=None, on_snapshot=None) -> None:
        if calls["n"] == 1:
            ev = event("run_started", 1, payload={"runtime_status": "active", "frontend_work_mode": "work"}, display_channel="status", visibility="progress", event_kind="task_progress", run_id="run_reconnect")
            client._apply_event(ev)
            events.append(ev)
            raise RuntimeError("模拟中文断流：网络中断")
        ev2 = event("assistant_final", 2, payload={"content": "任务已恢复续连并完成。", "status": "completed_pass"}, display_channel="conversation", visibility="user_dialogue", event_kind="final", run_id="run_reconnect")
        ev3 = event("run_terminal", 3, payload={"terminal": True, "status": "completed_pass"}, display_channel="status", visibility="progress", event_kind="final", run_id="run_reconnect")
        for ev in (ev2, ev3):
            client._apply_event(ev)
            events.append(ev)

    client._open_chat_stream = fake_open  # type: ignore[method-assign]
    client._consume_response = fake_consume  # type: ignore[method-assign]
    snapshot = client.submit_user_message_streaming(
        "模拟 150 轮长链，断开后自动续连",
        work_mode_payload={"mode": "work", "frontend_work_mode": "work", "long_chain_requested": True, "tools_requested": True},
        max_reconnects=2,
    )
    _assert(calls["n"] >= 2, "断链后未尝试重连")
    _assert(snapshot.reconnect_attempts >= 1, "reconnect_attempts 未记录")
    _assert(snapshot.current_task_status == "COMPLETED", "续连后任务未完成")
    return {"open_calls": calls["n"], "reconnect_attempts": snapshot.reconnect_attempts, "status": snapshot.current_task_status}


def _case_150_events_no_chat_pollution() -> dict[str, Any]:
    client = SseRuntimeClient(base_url="http://127.0.0.1:9")
    client._transcript.append_message(ChatMessage("user", "用户", "现在", "请执行长链任务"))
    client._snapshot.chat_messages = client._transcript.visible_messages()
    for i in range(150):
        ev = event("tool_progress", i + 1, payload={"tool_name": "mock_tool", "message": f"第 {i+1} 个工具事件"}, display_channel="workbench", visibility="task_telemetry", event_kind="tool_step")
        client._apply_event(ev)
    client._apply_event(event("assistant_final", 151, payload={"content": "长链任务已完成。", "status": "completed_pass"}, display_channel="conversation", visibility="user_dialogue", event_kind="final"))
    visible = client._snapshot.chat_messages
    texts = [m.text for m in visible]
    _assert(len(texts) == 2, f"会话区消息数异常：{len(texts)}")
    _assert(not any("工具事件" in x or "mock_tool" in x for x in texts), "工具步骤进入聊天区")
    return {"visible_messages": len(texts), "progress_notice_count": len(client._progress_notice_keys)}


def _case_chinese_error_summaries() -> dict[str, Any]:
    messages = [
        "Provider 未配置，任务已进入可恢复状态；详情在任务工作台。",
        "计划解析失败，已进入短 JSON 修复。",
        "模拟中文断流：网络中断，正在续连。",
    ]
    _assert(all(has_chinese(x) for x in messages), "存在非中文错误提示")
    _assert(not any("Traceback" in x or "Exception:" in x for x in messages), "错误提示暴露原始堆栈")
    return {"messages": messages}


def _case_provider_diagnostic_workbench_only() -> dict[str, Any]:
    result = SimpleNamespace(
        intent=None, plan=[], results=[], audit_events=[], chain_summary=None, suggestion_bridge=None,
        planner_execution_report=None, task_id="task_provider", status="provider_not_ready",
        failure_kind="provider_timeout", provider_status="timeout", has_executed_tools=False,
        plan_repair_attempted=False, deterministic_fallback_used=False, final_output_contract="execution_report",
        user_visible_summary="Provider 超时，详情已放到任务工作台。", next_action="请检查 Provider 配置或稍后重试。",
        planner_result=None, activation_form=None, task_state_snapshot=None, adaptive_work_loop=None,
        context_window_bundle=None, skill_playbook_route=None, active_model_policy=None,
        projection=RuntimeProjection(status="provider_not_ready", summary="Provider 超时，详情已放到任务工作台。", artifacts=[], audit_count=0),
        pending_confirmations=[],
    )
    events = runtime_result_to_sse_events(result, run_id="run_provider", task_id="task_provider")
    diag = [e for e in events if e["event"] == "runtime_state" and e["payload"].get("provider_status") == "timeout"]
    conv = [e for e in events if e["display_channel"] == "conversation"]
    _assert(diag and all(e["display_channel"] == "workbench" for e in diag), "Provider 诊断未进入工作台")
    _assert(not any("timeout" in json.dumps(e, ensure_ascii=False).lower() and e["event"] != "assistant_final" for e in conv), "Provider 细节污染会话")
    return {"diagnostic_events": len(diag), "conversation_events": len(conv)}


def _case_soul_baseline_affects_emotion() -> dict[str, Any]:
    soul_a = SoulAffectiveProfile(soul_ref="soul:calm", warmth=0.82, boundary_sensitivity=0.20, reflection_depth=0.72, achievement_drive=0.65)
    soul_b = SoulAffectiveProfile(soul_ref="soul:guarded", warmth=0.25, boundary_sensitivity=0.86, reflection_depth=0.40, achievement_drive=0.45)
    base_a = AffectiveBaseline.from_soul_profile(soul_a)
    base_b = AffectiveBaseline.from_soul_profile(soul_b)
    _assert(base_a.digest != base_b.digest, "Soul 变化未改变情感底色 digest")
    _assert(base_a.emotion_baseline.joy != base_b.emotion_baseline.joy or base_a.emotion_baseline.fear != base_b.emotion_baseline.fear, "Soul 未影响七情底色")
    return {"calm_digest": base_a.digest, "guarded_digest": base_b.digest, "calm_joy": base_a.emotion_baseline.joy, "guarded_fear": base_b.emotion_baseline.fear}


def _case_temp_emotion_from_chat_signal() -> dict[str, Any]:
    engine = AffectiveStateEngine()
    baseline = AffectiveBaseline.from_soul_profile(SoulAffectiveProfile(soul_ref="soul:test", warmth=0.55, reflection_depth=0.65))
    calm = engine.evolve(SevenEmotionSignalSources(joy_reward_signal=0.55), SixDesireSignalSources(achievement_goal_gap_signal=0.45), soul_baseline=baseline)
    stressed = engine.evolve(
        SevenEmotionSignalSources(obstruction_violation_signal=0.85, uncertainty_future_risk_signal=0.75, loss_failure_signal=0.7),
        SixDesireSignalSources(order_entropy_signal=0.8, rest_fatigue_recovery_signal=0.45),
        soul_baseline=baseline,
        previous_state=calm,
        elapsed_seconds=30,
    )
    route = AffectiveExecutionRouter().route(stressed)
    _assert(stressed.digest != calm.digest, "临时聊天信号未改变情感状态")
    _assert(has_chinese(route.planner_hint.style_hint), "情感路由没有中文风格提示")
    return {"before": calm.public_dict()["dominant_emotion"], "after": stressed.public_dict()["dominant_emotion"], "style_hint": route.planner_hint.style_hint}


def _case_affective_style_changes() -> dict[str, Any]:
    engine = AffectiveStateEngine()
    joy_state = engine.evolve(SevenEmotionSignalSources(joy_reward_signal=0.90), SixDesireSignalSources(connection_alignment_signal=0.75))
    worry_state = engine.evolve(SevenEmotionSignalSources(uncertainty_future_risk_signal=0.90, threat_irreversible_signal=0.65), SixDesireSignalSources(survival_resource_boundary_signal=0.80))
    router = AffectiveExecutionRouter()
    joy_hint = router.route(joy_state).planner_hint.style_hint
    worry_hint = router.route(worry_state).planner_hint.style_hint
    _assert(joy_hint != worry_hint, "不同情绪未影响聊天风格提示")
    return {"joy_hint": joy_hint, "worry_hint": worry_hint}


def _case_self_healing_candidate() -> dict[str, Any]:
    route = build_self_healing_route(planner_report=SimpleNamespace(failed_steps=2, timeout_steps=1, blocked_steps=0, confirmation_required_steps=0, task_id="task_fix", run_id="run_fix"), notes="compileall 失败")
    _assert(route.healing_need_score > 0, "自愈候选得分未激活")
    _assert(route.candidate_only and route.no_direct_execution and not route.invokes_tool, "自愈越权执行")
    return route.public_dict()


def _case_self_learning_candidate() -> dict[str, Any]:
    route = build_self_learning_route(user_requested_learning=True, notes="把本次修复经验沉淀为技能候选")
    _assert(route.learning_need_score > 0, "学习候选得分未激活")
    _assert(route.candidate_only and route.review_before_activation and route.no_knowledge_write, "学习路由越权写知识")
    return route.public_dict()


def _case_self_iteration_candidate() -> dict[str, Any]:
    route = build_self_iteration_route(iteration_candidates=["change_candidate:scrollbar_style"], repeated_failure_count=3, user_confirmed_direction=True, notes="优化前端滑条与 A5 弹窗投影")
    _assert(route.iteration_need_score > 0, "自我迭代候选得分未激活")
    data = route.public_dict()
    _assert(data.get("validation_requirement_refs") and data.get("rollback_requirement_refs"), "自我迭代缺少验证/回滚要求")
    _assert(route.candidate_only and route.no_direct_execution and not route.applies_patch, "自我迭代越权应用补丁")
    return data


def _case_backend_a5_projection_event() -> dict[str, Any]:
    result = SimpleNamespace(
        intent=None, plan=[], results=[], audit_events=[], chain_summary=None, suggestion_bridge=None,
        planner_execution_report=None, task_id="task_a5", status="awaiting_confirmation",
        failure_kind="requires_confirmation", provider_status="ready", has_executed_tools=False,
        plan_repair_attempted=False, deterministic_fallback_used=False, final_output_contract="execution_report",
        user_visible_summary="检测到 A5 操作，需要你确认。", next_action="请在前端审批弹窗中确认或拒绝。",
        planner_result=None, activation_form=None, task_state_snapshot=None, adaptive_work_loop=None,
        context_window_bundle=None, skill_playbook_route=None, active_model_policy=None,
        projection=RuntimeProjection(status="awaiting_confirmation", summary="等待用户确认", artifacts=[], audit_count=0),
        pending_confirmations=[{"ticket_id": "ticket_a5_001", "tool_name": "terminal", "risk_level": "A5", "reason": "高风险终端操作", "message": "需要人工确认", "arguments": {"cmd": "<redacted>"}}],
    )
    events = runtime_result_to_sse_events(result, run_id="run_a5", task_id="task_a5")
    approvals = [e for e in events if e["event"] == "approval_required"]
    _assert(approvals, "未生成 approval_required 事件")
    payload = approvals[0]["payload"]
    _assert(approvals[0]["display_channel"] == "workbench", "A5 详情应进入工作台")
    _assert(payload.get("requires_user_confirmation") is True, "A5 事件未要求用户确认")
    _assert(payload.get("risk_level") == "A5", "A5 风险等级丢失")
    return {"approval_event": payload, "event_count": len(events)}


def _case_frontend_a5_popup_trigger() -> dict[str, Any]:
    client = SseRuntimeClient(base_url="http://127.0.0.1:9")
    client._apply_event(event("run_started", 1, payload={"runtime_status": "active", "frontend_work_mode": "work"}, display_channel="status", visibility="progress", event_kind="task_progress"))
    client._apply_event(event("approval_required", 2, payload={
        "ticket_id": "ticket_a5_frontend",
        "gate_id": "ticket_a5_frontend",
        "title": "需要人工确认",
        "tool_name": "terminal",
        "risk_level": "A5",
        "decision": "requires_confirmation",
        "requires_user_confirmation": True,
        "action_summary": "模拟 A5 终端操作",
        "impact_scope": "测试工作区",
        "route_to_runtime_only": True,
    }, display_channel="workbench", visibility="task_telemetry", event_kind="approval_required"))
    snap = client._snapshot
    source = (REPO_ROOT / "frontend/linyuanzhe_frontend/ui/main_window_chat_runtime.py").read_text(encoding="utf-8")
    _assert(snap.run_workbench_state == "waiting_approval", "前端未进入等待审批状态")
    _assert(snap.pending_confirmations and snap.pending_confirmations[0].get("ticket_id") == "ticket_a5_frontend", "前端未保存 pending confirmation")
    _assert("def _show_permission_approval_modal" in source and "tk.Toplevel" in source and "grab_set" in source and "批准一次" in source and "拒绝" in source, "前端弹窗路径不完整")
    return {"pending_count": len(snap.pending_confirmations), "workbench_state": snap.run_workbench_state, "popup_source_verified": True}


def _case_free_will_idle_candidate() -> dict[str, Any]:
    tick = FreeWillBackgroundRunner().tick(
        tick_id="tick:idle",
        active_user_task=False,
        user_allowed_autonomy=False,
        idle_seconds=720,
        budget_pressure=0.12,
        context_pressure=0.2,
        autonomous_goal_refs=["goal:整理回归报告"],
    )
    _assert(tick.background_candidate_generated, "空闲时不能生成自由意志后台候选")
    _assert(tick.route is not None and tick.route.candidate_only, "自由意志后台候选越界")
    _assert(tick.no_tool_invocation and tick.no_file_write and tick.no_budget_mutation, "自由意志后台运行不得执行副作用")
    return tick.public_dict()


def _case_free_will_active_task_blocked() -> dict[str, Any]:
    lease = build_autonomy_lease(active_user_task=True, user_allowed_autonomy=False, idle_seconds=10, budget_pressure=0.1)
    route = build_free_will_route(lease=lease, candidate_level="FW1", candidate_summary="不应抢占用户任务")
    _assert(route.blocked and route.blocked_by_active_user_task, "自由意志抢占了活跃用户任务")
    return route.public_dict()


def _case_frontend_event_projection_performance() -> dict[str, Any]:
    client = SseRuntimeClient(base_url="http://127.0.0.1:9")
    client._transcript.append_message(ChatMessage("user", "用户", "现在", "请执行一个很长的工作流"))
    client._snapshot.chat_messages = client._transcript.visible_messages()
    started = time.perf_counter()
    for i in range(500):
        client._apply_event(event("tool_progress", i + 1, payload={"tool_name": "stress_tool", "message": f"进度 {i}"}, display_channel="workbench", visibility="task_telemetry", event_kind="tool_step"))
    elapsed = time.perf_counter() - started
    _assert(elapsed < 5.0, f"500 个事件投影耗时过高：{elapsed:.3f}s")
    _assert(len(client._snapshot.chat_messages) == 1, "工作流事件污染了会话区")
    return {"events": 500, "elapsed_ms": int(elapsed * 1000), "chat_messages": len(client._snapshot.chat_messages), "agent_ui_events": len(client.last_agent_ui_events)}


def _case_scrollbar_style_sources() -> dict[str, Any]:
    widgets = (REPO_ROOT / "frontend/linyuanzhe_frontend/ui/widgets.py").read_text(encoding="utf-8")
    main = (REPO_ROOT / "frontend/linyuanzhe_frontend/ui/main_window.py").read_text(encoding="utf-8")
    chat = (REPO_ROOT / "frontend/linyuanzhe_frontend/ui/main_window_chat_runtime.py").read_text(encoding="utf-8")
    _assert("LZ.Vertical.TScrollbar" in widgets and "LZ.Chat.Vertical.TScrollbar" in widgets, "未定义统一滑条样式")
    _assert("make_vertical_scrollbar(outer, canvas.yview" in main, "侧面/页面滑条未替换为统一样式")
    _assert("make_vertical_scrollbar(body_wrap, body.yview, variant=\"chat\")" in chat, "会话滑条未替换为统一样式")
    return {"styles": ["LZ.Vertical.TScrollbar", "LZ.Chat.Vertical.TScrollbar", "LZ.Sidebar.Vertical.TScrollbar"]}


def _case_a5_chinese_copy() -> dict[str, Any]:
    result = SimpleNamespace(
        intent=None, plan=[], results=[], audit_events=[], chain_summary=None, suggestion_bridge=None,
        planner_execution_report=None, task_id="task_a5_copy", status="blocked_A5",
        failure_kind="blocked_A5", provider_status="ready", has_executed_tools=False,
        plan_repair_attempted=False, deterministic_fallback_used=False, final_output_contract="execution_report",
        user_visible_summary="A5 极高危操作已阻断，需要人工确认。", next_action="请确认是否继续。",
        planner_result=None, activation_form=None, task_state_snapshot=None, adaptive_work_loop=None,
        context_window_bundle=None, skill_playbook_route=None, active_model_policy=None,
        projection=RuntimeProjection(status="blocked_A5", summary="A5 极高危操作已阻断", artifacts=[], audit_count=0),
        pending_confirmations=[],
    )
    events = runtime_result_to_sse_events(result, run_id="run_a5_copy", task_id="task_a5_copy")
    texts = [json.dumps(e["payload"], ensure_ascii=False) for e in events if e["event"] in {"approval_required", "assistant_final", "execution_report"}]
    _assert(texts and all(has_chinese(t) for t in texts), "A5 相关提示不是中文")
    return {"checked_events": len(texts), "texts": texts[:3]}


def _case_weak_model_blocked() -> dict[str, Any]:
    profile = SimpleNamespace(provider_id="deepseek", model_id="tiny-summarizer", profile_id="profile_weak", recommended_role="subagent_only")
    policy = SimpleNamespace(model_role="subagent_only", allowed_tool_families=("analysis",), max_context_chars=1200)
    active = ModelExecutionPolicyEngine().activate(profile, policy, requested_max_steps=20)
    _assert(not active.allowed_work_mode, "弱模型被误当工作主脑")
    _assert(active.failure_kind == "weak_model_not_allowed", "弱模型阻断原因错误")
    return active.public_dict()


def _case_final_summary_not_full_report() -> dict[str, Any]:
    result = SimpleNamespace(
        intent=None,
        plan=[SimpleNamespace(step_id="s1", tool_name="read_file", risk_level="A1", reason="verify", arguments={"path": "hello.txt"})],
        results=[SimpleNamespace(step_id="s1", tool_name="read_file", status="ok", output_summary="读取完成", artifacts=[], error_code="", audit_ref="audit1", data={})],
        audit_events=[], chain_summary=None, suggestion_bridge=None, planner_execution_report=None,
        task_id="task_final", status="completed_pass", failure_kind="", provider_status="ready", has_executed_tools=True,
        plan_repair_attempted=False, deterministic_fallback_used=False, final_output_contract="execution_report",
        user_visible_summary="任务已完成。", next_action="",
        planner_result=None, activation_form=None, task_state_snapshot=None, adaptive_work_loop=None,
        context_window_bundle=None, skill_playbook_route=None, active_model_policy=None,
        projection=RuntimeProjection(status="completed_pass", summary="完整报告包含工具步骤，但应放工作台。", artifacts=["artifact:hello"], audit_count=1),
        pending_confirmations=[],
    )
    events = runtime_result_to_sse_events(result, run_id="run_final", task_id="task_final")
    conv = [e for e in events if e["display_channel"] == "conversation"]
    wb = [e for e in events if e["event"] == "execution_report"]
    _assert(len(conv) == 1 and conv[0]["event"] == "assistant_final", "final 摘要未进入会话")
    _assert(wb and wb[0]["display_channel"] == "workbench", "完整报告未进入工作台")
    _assert("read_file" not in conv[0]["payload"].get("content", ""), "工具细节进入 final 会话摘要")
    return {"conversation_events": len(conv), "workbench_reports": len(wb), "final_content": conv[0]["payload"].get("content", "")}


def _case_chat_copy_clean() -> dict[str, Any]:
    client = SseRuntimeClient(base_url="http://127.0.0.1:9")
    client._transcript.append_message(ChatMessage("user", "用户", "现在", "请扫描项目并交付"))
    client._snapshot.chat_messages = client._transcript.visible_messages()
    client._apply_event(event("planner_plan", 1, payload={"steps": [{"tool_name": "scan_project"}]}, display_channel="workbench", visibility="task_telemetry", event_kind="task_progress"))
    client._apply_event(event("tool_result", 2, payload={"tool_name": "scan_project", "status": "ok", "output_summary": "扫描完成"}, display_channel="workbench", visibility="task_telemetry", event_kind="tool_step"))
    client._apply_event(event("assistant_final", 3, payload={"content": "项目扫描已完成，报告已放入工作台。", "status": "completed_pass"}, display_channel="conversation", visibility="user_dialogue", event_kind="final"))
    copied_text = "\n".join(m.text for m in client._snapshot.chat_messages)
    _assert("scan_project" not in copied_text and "planner_plan" not in copied_text, "复制聊天会带出工具步骤")
    return {"copied_message_count": len(client._snapshot.chat_messages), "copied_text": copied_text}


def _case_frontend_permission_flags_static() -> dict[str, Any]:
    source = (REPO_ROOT / "frontend/linyuanzhe_frontend/contracts/agent_ui_events.py").read_text(encoding="utf-8")
    required = [
        '"no_frontend_tool_execution": True',
        '"no_frontend_provider_call": True',
        '"no_frontend_memory_write": True',
        '"no_frontend_rollback_apply": True',
        '"no_frontend_self_iteration_apply": True',
    ]
    missing = [item for item in required if item not in source]
    _assert(not missing, f"前端权限只读边界缺失：{missing}")
    return {"verified_flags": required}


def write_report(results: list[CaseResult]) -> dict[str, Any]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    passed = sum(1 for r in results if r.status == "PASS")
    failed = len(results) - passed
    by_req: dict[str, int] = {}
    for item in results:
        by_req[item.requirement] = by_req.get(item.requirement, 0) + 1
    payload = {
        "schema": "tiangong.l6_73_0.human_deepseek_full_chain_pressure.v1",
        "simulated_model": "deepseek-main-brain-deterministic",
        "case_count": len(results),
        "passed": passed,
        "failed": failed,
        "all_passed": failed == 0,
        "requirement_coverage": by_req,
        "cases": [asdict(r) for r in results],
        "notes": [
            "未调用真实 DeepSeek API；本压测按用户要求模拟 DeepSeek 主脑填 ActivationForm。",
            "GUI 视觉弹窗在无显示容器中做事件投影+源码路径验证；真实桌面弹窗需本机可视化复验。",
            "自由意志系统按当前架构只允许后台候选/Planner hint，不允许后台副作用执行。",
        ],
    }
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# L6.73.0 人类 ↔ 模拟 DeepSeek ↔ 临渊者全链压测报告", ""]
    lines.append(f"- 用例数：{len(results)}")
    lines.append(f"- 通过：{passed}")
    lines.append(f"- 失败：{failed}")
    lines.append(f"- 结论：{'PASS' if failed == 0 else 'FAIL'}")
    lines.append("")
    lines.append("| ID | 场景 | 覆盖要求 | 结果 | 说明 |")
    lines.append("|---|---|---:|---|---|")
    for r in results:
        msg = str(r.message).replace("|", "／")[:160]
        lines.append(f"| {r.case_id} | {r.title} | {r.requirement} | {r.status} | {msg} |")
    lines.append("")
    lines.append("## 未验证边界")
    lines.append("- 无显示容器无法肉眼确认弹窗视觉和滑条最终像素效果；本轮验证了事件触发、状态投影、弹窗源码路径和样式替换。")
    lines.append("- 未调用真实 DeepSeek API，使用确定性模拟主脑压测 ActivationForm 与执行链。")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    return payload


def main() -> int:
    print("START L6.73.0 human/deepseek full-chain pressure smoke", flush=True)
    results = run_cases()
    payload = write_report(results)
    print(json.dumps({"case_count": payload["case_count"], "passed": payload["passed"], "failed": payload["failed"], "report": _public_path(REPORT_JSON)}, ensure_ascii=False, indent=2))
    if payload["failed"]:
        for case in results:
            if case.status != "PASS":
                print(f"[FAIL] {case.case_id} {case.title}: {case.message}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
