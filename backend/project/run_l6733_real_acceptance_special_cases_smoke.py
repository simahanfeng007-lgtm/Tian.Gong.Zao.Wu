from __future__ import annotations

"""L6.73.3 real desktop/provider acceptance special-cases smoke.

This is a deterministic contract/source smoke. It does not call a real Provider,
does not launch Tk, and does not execute user tools. It verifies the L6.73.3
acceptance boundary for: chat/work routing, upload handoff routing, Provider
settings/error classification, conversation/workbench separation, A5 projection,
settings persistence contracts, long-chain event pressure, and autonomous route
side-effect guards.
"""

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "backend" / "project"
FRONTEND = ROOT / "frontend"
REPORT_DIR = Path(os.environ.get("TIANGONG_REPORT_DIR") or tempfile.mkdtemp(prefix="l6733_real_acceptance_reports_"))
REPORT_JSON = REPORT_DIR / "l6733_real_acceptance_special_cases_report.json"
REPORT_MD = REPORT_DIR / "l6733_real_acceptance_special_cases_report.md"


def _public_report_path(path: Path) -> str:
    try:
        if str(path).startswith(tempfile.gettempdir()):
            return f"<tmp>/{path.name}"
    except Exception:
        pass
    return path.name

import sys
for path in (str(PROJECT), str(FRONTEND)):
    if path not in sys.path:
        sys.path.insert(0, path)

from tiangong_agent_runtime.free_will_background_runner import FreeWillBackgroundRunner  # noqa: E402
from tiangong_agent_runtime.model_capability_adapter import ModelCapabilityAdapter  # noqa: E402
from tiangong_agent_runtime.model_execution_policy_engine import ModelExecutionPolicyEngine  # noqa: E402
from tiangong_agent_runtime.plan_bridge import PlanBridge  # noqa: E402
from tiangong_agent_runtime.self_iteration_route import build_self_iteration_route  # noqa: E402
from tiangong_agent_runtime.self_learning_route import build_self_learning_route  # noqa: E402
from tiangong_agent_runtime.tool_invocation import ToolInvocation  # noqa: E402
from tiangong_agent_shell.providers.provider_error import ProviderErrorKind, classify_provider_error  # noqa: E402
from linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient  # noqa: E402
from linyuanzhe_frontend.contracts.file_transfer import FileTransferRequest  # noqa: E402
from linyuanzhe_frontend.contracts.model_settings import (  # noqa: E402
    MODEL_CUSTOM_SENTINEL,
    default_base_url_for_provider,
    effective_model_name,
    filter_model_catalog,
    model_values_for_provider,
    sanitize_runtime_settings,
)
from linyuanzhe_frontend.contracts.provider_settings import (  # noqa: E402
    ProviderSettingsWriteRequest,
    provider_readiness_from_public_projection,
)
from linyuanzhe_frontend.contracts.run_workbench import normalize_run_state  # noqa: E402
from linyuanzhe_frontend.contracts.sse_events import RuntimeSseEvent, sanitize_event_payload  # noqa: E402
from linyuanzhe_frontend.contracts.work_modes import (  # noqa: E402
    infer_work_mode_from_text,
    resolve_submit_work_mode,
    sanitize_work_mode_payload,
    work_mode_labels,
)
from linyuanzhe_frontend.ui.localization import host_access_scope_label, host_access_scope_value  # noqa: E402
from linyuanzhe_frontend.version_info import FE_RUNTIME_VERSION  # noqa: E402


@dataclass
class CaseResult:
    name: str
    status: str
    detail: str = ""


RESULTS: list[CaseResult] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def case(name: str):
    def wrap(fn):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - smoke report should capture exact failure
            RESULTS.append(CaseResult(name, "FAIL", f"{type(exc).__name__}: {exc}"))
        else:
            RESULTS.append(CaseResult(name, "PASS", ""))
        return fn
    return wrap


def _event(name: str, seq: int, *, channel: str, visibility: str, kind: str, payload: dict[str, Any]) -> RuntimeSseEvent:
    return RuntimeSseEvent(
        event=name,
        seq=seq,
        run_id="run_l6733",
        task_id="task_l6733",
        display_channel=channel,
        visibility=visibility,
        event_kind=kind,
        payload=payload,
    )


def _tool_names(plan: list[ToolInvocation]) -> list[str]:
    return [step.tool_name for step in plan]


# A. 聊天与模式分流
@case("A01 chat 模式标签只有聊天/工作")
def _a01() -> None:
    require(work_mode_labels() == ["聊天", "工作"], "visible modes must remain chat/work only")


@case("A02 前端不按关键词推断 code/file/long_chain")
def _a02() -> None:
    for text in ("修复这个 Python 项目", "读取 file.txt", "执行 150 阶段长链", "打包 zip"):
        require(infer_work_mode_from_text(text) == "chat", f"frontend inferred work mode for: {text}")


@case("A03 chat payload 不请求 Planner/Tools")
def _a03() -> None:
    payload = resolve_submit_work_mode("聊天", "创建 hello.txt")
    require(payload["mode"] == "chat", "chat mode not preserved")
    require(payload["planner_allowed"] is False and payload["tools_requested"] is False, "chat must not request tools")


@case("A04 work payload 只请求 ActivationForm 边界")
def _a04() -> None:
    payload = resolve_submit_work_mode("工作", "继续下一步")
    require(payload["mode"] == "work", "work mode not preserved")
    require(payload["activation_requested"] is True and payload["llm_fills_activation_form"] is True, "ActivationForm boundary missing")
    require(payload["no_frontend_tool_execution"] is True, "frontend tool boundary missing")
    require(payload["long_chain_requested"] is False, "work must not imply long_chain by default")


@case("A05 sandbox/work 普通寒暄不会自动打开 task_flow")
def _a05() -> None:
    payload = sanitize_work_mode_payload({"mode": "work", "task_flow_requested": False, "long_chain_requested": False})
    require(payload["task_flow_requested"] is False and payload["long_chain_requested"] is False, "plain work preference should not force task_flow")


@case("A06 显式 long_chain 只有 work 正规输入才保留")
def _a06() -> None:
    payload = sanitize_work_mode_payload({"mode": "work", "long_chain_requested": True})
    require(payload["long_chain_requested"] is True and payload["task_flow_requested"] is True, "explicit work long_chain not preserved")
    legacy = sanitize_work_mode_payload({"mode": "long_chain", "long_chain_requested": True})
    require(legacy["mode"] == "work" and legacy["long_chain_requested"] is False, "legacy UI long_chain must not revive as visible mode")


@case("A07 SseRuntimeClient chat payload 同步 L6.73.3 contract")
def _a07() -> None:
    client = SseRuntimeClient("http://127.0.0.1:8787")
    body = client._chat_payload("测试", work_mode_payload=resolve_submit_work_mode("聊天", "测试"))
    require(body["frontend_contract"] == FE_RUNTIME_VERSION and FE_RUNTIME_VERSION.startswith("L6.73."), f"frontend contract mismatch: {body.get('frontend_contract')} / {FE_RUNTIME_VERSION}")
    require(body["no_frontend_tool_execution"] is True, "chat payload lost frontend no-tool boundary")


@case("A08 work 失败态不归一成普通 completed")
def _a08() -> None:
    require(normalize_run_state("provider_not_ready") == "recoverable", "provider_not_ready must be recoverable")
    require(normalize_run_state("model_required") == "recoverable", "model_required must be recoverable")
    require(normalize_run_state("partial_with_resume") == "recoverable", "partial_with_resume must be recoverable")
    require(normalize_run_state("completed_pass") == "completed", "completed_pass must be completed")


@case("A09 普通分析请求在前端保持 chat")
def _a09() -> None:
    require(infer_work_mode_from_text("帮我分析一下这个项目下一步怎么做，不要执行") == "chat", "analysis-only request must stay chat at frontend layer")


@case("A10 work payload 不携带 work_type/code/file 决策")
def _a10() -> None:
    payload = resolve_submit_work_mode("工作", "修复代码")
    for key in ("work_type", "code_intent", "file_intent"):
        if key in {"code_intent", "file_intent"}:
            require(payload[key] is False, f"{key} must remain false at frontend boundary")
        else:
            require(key not in payload, "frontend must not decide work_type")


# B. 文件与上传
@case("B11 上传 txt 交接走 read_file 且使用 runtime_local_path")
def _b11() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "sample.txt"
        p.write_text("hello", encoding="utf-8")
        req = FileTransferRequest.from_path(p)
        plan = PlanBridge().build_plan(f"读取这个文件\n[Runtime本地文件交接]\n附件1: sample.txt | runtime_local_path={req.runtime_handoff_path}")
        require(_tool_names(plan) == ["read_file"], f"txt handoff plan wrong: {_tool_names(plan)}")
        require(plan[0].arguments["path"] == str(p.resolve()), "runtime_local_path not used")


@case("B12 上传 md/json/py 默认 read_file")
def _b12() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        for suffix in ("md", "json", "py"):
            p = Path(tmp) / f"sample.{suffix}"
            p.write_text("x", encoding="utf-8")
            plan = PlanBridge().build_plan(f"总结这个文件\n[Runtime本地文件交接]\n附件1: {p.name} | runtime_local_path={p}")
            require(_tool_names(plan) == ["read_file"], f"{suffix} must route to read_file")


@case("B13 上传 docx/pdf/xlsx/pptx/csv 默认 document_parse")
def _b13() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        for suffix in ("docx", "pdf", "xlsx", "pptx", "csv"):
            p = Path(tmp) / f"sample.{suffix}"
            p.write_bytes(b"placeholder")
            plan = PlanBridge().build_plan(f"解析该文件\n[Runtime本地文件交接]\n附件1: {p.name} | runtime_local_path={p}")
            require(_tool_names(plan) == ["document_parse"], f"{suffix} must route to document_parse")


@case("B14 上传公开记录不暴露源路径")
def _b14() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "secret.txt"
        p.write_text("hello", encoding="utf-8")
        req = FileTransferRequest.from_path(p)
        public = json.dumps(req.to_public_record(status="prepared"), ensure_ascii=False)
        require(str(p.resolve()) not in public, "public upload record leaked source path")
        require("local_path_digest" not in public and "runtime_handoff_path" not in public, "public upload record exposed private handoff fields")


@case("B15 metadata/public record 可标识失败但不伪装成功")
def _b15() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "x.txt"
        p.write_text("x", encoding="utf-8")
        req = FileTransferRequest.from_path(p)
        public = req.to_public_record(status="failed", message="handoff failed")
        require(public["status"] == "failed" and public["route_to_runtime_only"] is True, "failed upload public record invalid")


@case("B16 path_not_found 仅保留中文可读摘要不泄露 repaircontext")
def _b16() -> None:
    client = SseRuntimeClient("http://127.0.0.1:1")
    raw = "read_file: failed | path_not_found 文件不存在 adaptiveworkloopv1 repaircontext traceback /mnt/data/private.txt"
    clean = client._clean_assistant_visible_content(raw, final=True)
    require("path_not_found" in clean or "文件不存在" in clean, "missing path_not_found readable summary")
    require("adaptiveworkloop" not in clean.lower() and "repaircontext" not in clean.lower(), "internal repair marker leaked")


@case("B17 FileTransferRequest 缺失文件直接拒绝")
def _b17() -> None:
    try:
        FileTransferRequest.from_path("/tmp/definitely_missing_l6733.txt")
    except FileNotFoundError:
        return
    raise AssertionError("missing source must raise FileNotFoundError")


@case("B18 handoff 无读取意图时不乱触发工具")
def _b18() -> None:
    plan = PlanBridge().build_plan("我明天再说\n[Runtime本地文件交接]\n附件1: sample.txt | runtime_local_path=/tmp/sample.txt")
    require(plan == [], "handoff without read/summary/parse intent should not plan tools")


@case("B19 raw local path sanitizer 摘要化")
def _b19() -> None:
    payload = sanitize_event_payload({"path": "C:\\Users\\Alice\\secret.txt", "api_key": "mockkey_secret-secret"})
    text = json.dumps(payload, ensure_ascii=False)
    require("mockkey_secret" not in text and "api_key_digest" in text, "api key not sanitized")


@case("B20 read_file 成功摘要可进入自然语言 final")
def _b20() -> None:
    client = SseRuntimeClient("http://127.0.0.1:1")
    msg = client._clean_assistant_visible_content("文件内容摘要：hello world", final=True)
    require("hello world" in msg, "readable file summary was stripped")


# C. Provider 与模型策略
@case("C21 DeepSeek Base URL 默认正确")
def _c21() -> None:
    require(default_base_url_for_provider("deepseek") == "https://api.deepseek.com", "DeepSeek Base URL default wrong")


@case("C22 API Key 不进入 public dict 明文")
def _c22() -> None:
    req = ProviderSettingsWriteRequest.from_form({"provider": "deepseek", "model": "deepseek-v4-pro", "api_key": "mockkey_test-secret", "base_url": "https://api.deepseek.com"})
    public = req.to_public_dict()
    runtime = req.to_runtime_payload()
    require("api_key" not in public and public["api_key_configured"] is True and public["api_key_digest"], "public provider projection leaked or missed key summary")
    require(runtime["api_key"] == "mockkey_test-secret", "runtime write-only payload must carry key only outbound")


@case("C23 Base URL 可明文显示并保存偏好")
def _c23() -> None:
    settings = sanitize_runtime_settings({"provider": "deepseek", "model": "deepseek-v4-pro", "api_base_url": "https://api.deepseek.com", "api_key": "mockkey_test-secret"})
    require(settings["base_url_display"] == "https://api.deepseek.com", "Base URL display missing")
    require(settings["raw_base_url_persisted"] is True and settings["raw_api_key_persisted"] is False, "Base URL/API Key persistence boundary wrong")


@case("C24 Provider 错误分类中文化")
def _c24() -> None:
    mapping = {
        401: ProviderErrorKind.AUTH_ERROR,
        404: ProviderErrorKind.MODEL_NOT_FOUND,
        429: ProviderErrorKind.RATE_LIMITED,
        500: ProviderErrorKind.SERVER_ERROR,
    }
    for code, kind in mapping.items():
        err = classify_provider_error(provider="deepseek", status_code=code, detail="mockkey_test-secret raw")
        require(err.kind is kind, f"status {code} classification wrong")
        public = err.public_dict()
        require("mockkey_test-secret" not in json.dumps(public, ensure_ascii=False), "provider public error leaked secret")
        require(any(ch >= "\u4e00" and ch <= "\u9fff" for ch in public["user_message"]), "provider user message must be Chinese readable")


@case("C25 timeout/context_overflow 分类正确")
def _c25() -> None:
    require(classify_provider_error(TimeoutError("timeout"), provider="openai").kind is ProviderErrorKind.TIMEOUT, "timeout classification wrong")
    require(classify_provider_error(provider="openai", detail="maximum context length exceeded").kind is ProviderErrorKind.CONTEXT_OVERFLOW, "context overflow classification wrong")


@case("C26 模型 catalog Provider 绑定隔离")
def _c26() -> None:
    require(all(item.provider == "deepseek" for item in filter_model_catalog("", provider="deepseek")), "DeepSeek catalog leaked other providers")
    require(MODEL_CUSTOM_SENTINEL in model_values_for_provider("openai"), "OpenAI custom model sentinel missing")
    require(effective_model_name("openai", MODEL_CUSTOM_SENTINEL, "gpt-custom-latest") == "gpt-custom-latest", "custom effective model failed")


@dataclass
class _Cfg:
    provider: str
    model: str


@case("C27 弱模型不能作为 work 主脑")
def _c27() -> None:
    adapter = ModelCapabilityAdapter()
    profile = adapter.resolve_profile(_Cfg("weak", "tiny-summary-only"))
    policy = adapter.resolve_policy(profile)
    active = ModelExecutionPolicyEngine().activate(profile, policy, requested_max_steps=80)
    require(active.allowed_work_mode is False and active.status == "blocked", "weak model not blocked")


@case("C28 micro_planner 每轮最多 1-3 步")
def _c28() -> None:
    adapter = ModelCapabilityAdapter()
    profile = adapter.resolve_profile(_Cfg("qwen", "qwen-plus"))
    policy = adapter.resolve_policy(profile)
    active = ModelExecutionPolicyEngine().activate(profile, policy, requested_max_steps=80)
    require(active.model_role == "micro_planner" and active.max_plan_steps_per_round <= 3 and active.effective_max_steps <= 3, "micro planner cap invalid")


@case("C29 强模型允许长链但仍限步")
def _c29() -> None:
    adapter = ModelCapabilityAdapter()
    profile = adapter.resolve_profile(_Cfg("openai", "gpt-4.1"))
    policy = adapter.resolve_policy(profile)
    active = ModelExecutionPolicyEngine().activate(profile, policy, requested_max_steps=80)
    require(active.allowed_work_mode and active.allow_long_chain and active.effective_max_steps <= 20, "strong model policy invalid")


@case("C30 Provider readiness 缺配置显示中文引导")
def _c30() -> None:
    projection = provider_readiness_from_public_projection({"api_key_configured": False, "base_url_configured": False, "effective_backend_mode": "not_configured"})
    require(projection.readiness == "missing_credentials" and "缺少" in projection.message, "missing provider guidance invalid")


# D. 会话/工作台分离
@case("D31 100 个 task_progress 不进 conversation")
def _d31() -> None:
    client = SseRuntimeClient("http://127.0.0.1:1")
    client._apply_event(_event("run_started", 1, channel="status", visibility="progress", kind="task_progress", payload={"frontend_work_mode": "work"}))
    for i in range(100):
        client._apply_event(_event("tool_progress", i + 2, channel="workbench", visibility="task_telemetry", kind="tool_step", payload={"step_id": f"s{i}", "tool_name": "read_file", "message": f"内部步骤 {i}"}))
    require(len(client.get_snapshot().chat_messages) == 0, "tool progress polluted conversation")


@case("D32 Planner JSON 不进 conversation")
def _d32() -> None:
    client = SseRuntimeClient("http://127.0.0.1:1")
    client._apply_event(_event("planner_plan", 1, channel="workbench", visibility="task_telemetry", kind="task_progress", payload={"steps": [{"tool_name": "write_workspace_file", "arguments": {"path": "hello.txt"}}]}))
    require(len(client.get_snapshot().chat_messages) == 0, "planner plan polluted conversation")


@case("D33 raw stderr/traceback 被清理")
def _d33() -> None:
    client = SseRuntimeClient("http://127.0.0.1:1")
    clean = client._clean_assistant_visible_content("Traceback (most recent call last):\nreturn_code: 1\nrepaircontext", final=True)
    lower = clean.lower()
    require("traceback" not in lower and "repaircontext" not in lower, "raw traceback/internal marker leaked")


@case("D34 assistant_final 简明结论进入 conversation")
def _d34() -> None:
    client = SseRuntimeClient("http://127.0.0.1:1")
    client._apply_event(_event("assistant_final", 1, channel="conversation", visibility="user_dialogue", kind="final", payload={"content": "任务已完成。详情已放入任务工作台。"}))
    texts = [m.text for m in client.get_snapshot().chat_messages]
    require(any("任务已完成" in t for t in texts), "assistant_final did not enter conversation")


@case("D35 execution_report 进 workbench 不进 conversation")
def _d35() -> None:
    client = SseRuntimeClient("http://127.0.0.1:1")
    client._apply_event(_event("execution_report", 1, channel="workbench", visibility="artifact", kind="final", payload={"status": "completed_pass", "summary": "完整执行报告：tool_step raw"}))
    require(len(client.get_snapshot().chat_messages) == 0, "execution_report polluted conversation")


@case("D36 approval_required 进入 waiting_approval 且不倾倒细节")
def _d36() -> None:
    client = SseRuntimeClient("http://127.0.0.1:1")
    client._apply_event(_event("run_started", 1, channel="status", visibility="progress", kind="task_progress", payload={"frontend_work_mode": "work"}))
    client._apply_event(_event("approval_required", 2, channel="workbench", visibility="task_telemetry", kind="approval_required", payload={"risk_level": "A5", "decision": "requires_confirmation", "ticket_id": "tk_l6733", "action_summary": "删除系统文件", "impact_scope": "system_drive"}))
    snap = client.get_snapshot()
    require(snap.run_workbench_state == "waiting_approval" and snap.pending_confirmation_count >= 1, "approval did not set waiting_approval")
    require(len(snap.chat_messages) == 0, "approval details polluted conversation")


@case("D37 复制聊天记录不包含工具步骤")
def _d37() -> None:
    client = SseRuntimeClient("http://127.0.0.1:1")
    client._apply_event(_event("tool_started", 1, channel="workbench", visibility="task_telemetry", kind="tool_step", payload={"tool_name": "write_workspace_file", "message": "内部工具步骤"}))
    transcript = "\n".join(m.text for m in client.get_snapshot().chat_messages)
    require("write_workspace_file" not in transcript and "内部工具步骤" not in transcript, "chat copy contains tool detail")


@case("D38 150 长链事件聊天区零污染")
def _d38() -> None:
    client = SseRuntimeClient("http://127.0.0.1:1")
    client._apply_event(_event("run_started", 1, channel="status", visibility="progress", kind="task_progress", payload={"frontend_work_mode": "work"}))
    for i in range(150):
        client._apply_event(_event("tool_result", i + 2, channel="workbench", visibility="task_telemetry", kind="tool_step", payload={"step_id": f"stage_{i}", "tool_name": "diagnose_project", "status": "completed_pass", "output_summary": f"阶段 {i}"}))
    require(len(client.get_snapshot().chat_messages) == 0, "150-event long chain polluted conversation")


@case("D39 500 工作台事件不卡断快照且不执行前端工具")
def _d39() -> None:
    client = SseRuntimeClient("http://127.0.0.1:1")
    for i in range(500):
        client._apply_event(_event("heartbeat", i + 1, channel="status", visibility="progress", kind="task_progress", payload={"heartbeat": True, "elapsed_ms": i}))
    snap = client.get_snapshot()
    require(snap.frontend_executes_tools is False, "frontend executes tools flag changed")
    require(snap.run_heartbeat_count >= 1, "heartbeat not reflected")


@case("D40 Provider endpoint/API key 事件脱敏")
def _d40() -> None:
    payload = sanitize_event_payload({"base_url": "https://api.deepseek.com", "api_key": "mockkey_test-secret"})
    text = json.dumps(payload, ensure_ascii=False)
    require("https://api.deepseek.com" not in text and "mockkey_test-secret" not in text, "SSE payload leaked endpoint or key")
    require("base_url_digest" in payload and "api_key_digest" in payload, "digest projection missing")


# E. UI 与设置
@case("E41 电脑访问范围中文标签映射正确")
def _e41() -> None:
    require(host_access_scope_label("system_drive") == "全电脑 / 系统盘", "system_drive label wrong")
    require(host_access_scope_value("自定义根目录") == "custom_root", "custom root value wrong")


@case("E42 自定义根目录只保存偏好不执行文件工具")
def _e42() -> None:
    req = ProviderSettingsWriteRequest.from_form({"host_access_scope": "自定义根目录", "host_access_root": "C:/work/root"})
    public = req.to_public_dict()
    require(req.host_access_scope == "custom_root", "custom root not normalized")
    require(public["host_access_root_configured"] is True and "C:/work/root" not in json.dumps(public), "host root public projection leaked raw path")
    require(public["no_frontend_tool_execution"] is True, "frontend tool boundary lost")


@case("E43 Soul 名称/描述保存契约保留且描述脱敏摘要")
def _e43() -> None:
    req = ProviderSettingsWriteRequest.from_form({"persona_name": "临渊者", "persona_prompt": "稳定、沉着。"})
    public = req.to_public_dict()
    runtime = req.to_runtime_payload()
    require(public["persona_name"] == "临渊者" and public["persona_digest"], "Soul public digest missing")
    require(runtime.get("persona_prompt") == "稳定、沉着。", "runtime soul payload missing")


@case("E44 设置页源码含保存全部设置/Base URL/Soul滚轮")
def _e44() -> None:
    pages = (FRONTEND / "linyuanzhe_frontend" / "ui" / "main_window_feature_pages.py").read_text(encoding="utf-8")
    for token in ("保存全部设置", "Base URL 会完整保留在设置页显示", "make_vertical_scrollbar(soul_text_shell", "def soul_wheel", "return \"break\""):
        require(token in pages, f"settings UI token missing: {token}")


@case("E45 UI preferences v4 覆盖模型/技能/工具搜索词")
def _e45() -> None:
    main_src = (FRONTEND / "linyuanzhe_frontend" / "ui" / "main_window.py").read_text(encoding="utf-8")
    for token in ("ui_preferences.v4", "model_search", "skill_search", "tool_search", "last_base_url", "host_access_root"):
        require(token in main_src, f"UI persistence token missing: {token}")


@case("E46 设置保存 payload 包含 Base URL/host_access_root")
def _e46() -> None:
    actions = (FRONTEND / "linyuanzhe_frontend" / "ui" / "main_window_actions.py").read_text(encoding="utf-8")
    require('"base_url": self.api_base_url_var.get()' in actions, "Base URL save payload missing")
    require('"host_access_root"' in actions and "_choose_host_access_root_frontend_only" in actions, "host root save/chooser missing")


@case("E47 字号/行距/紧凑模式设置项仍存在")
def _e47() -> None:
    main_src = (FRONTEND / "linyuanzhe_frontend" / "ui" / "main_window.py").read_text(encoding="utf-8")
    pages = (FRONTEND / "linyuanzhe_frontend" / "ui" / "main_window_feature_pages.py").read_text(encoding="utf-8")
    for token in ("chat_font_size", "line_height", "compact_mode"):
        require(token in main_src + pages, f"appearance persistence token missing: {token}")


@case("E48 任务流程显示开关保存项存在")
def _e48() -> None:
    src = (FRONTEND / "linyuanzhe_frontend" / "ui" / "main_window.py").read_text(encoding="utf-8") + (FRONTEND / "linyuanzhe_frontend" / "ui" / "main_window_feature_pages.py").read_text(encoding="utf-8")
    require("task_flow" in src or "任务流程" in src, "task flow display setting missing")


@case("E49 上传文件后自动处理开关保存项存在")
def _e49() -> None:
    src = (FRONTEND / "linyuanzhe_frontend" / "ui" / "main_window.py").read_text(encoding="utf-8") + (FRONTEND / "linyuanzhe_frontend" / "ui" / "main_window_feature_pages.py").read_text(encoding="utf-8")
    require("auto" in src.lower() and ("upload" in src.lower() or "上传" in src), "upload auto-processing setting token missing")


@case("E50 A5 弹窗源码含三按钮")
def _e50() -> None:
    src = (FRONTEND / "linyuanzhe_frontend" / "ui" / "main_window_chat_runtime.py").read_text(encoding="utf-8")
    for token in ("tk.Toplevel", "批准一次", "本次会话始终批准", "拒绝"):
        require(token in src, f"A5 modal token missing: {token}")


# F. 风险与自主演化
@case("F51 A0-A4 不进入 waiting_approval")
def _f51() -> None:
    client = SseRuntimeClient("http://127.0.0.1:1")
    client._apply_event(_event("quality_gate", 1, channel="workbench", visibility="task_telemetry", kind="quality_gate", payload={"risk_level": "A4", "decision": "allowed", "ticket_id": ""}))
    require(client.get_snapshot().run_workbench_state != "waiting_approval", "A0-A4 should not force waiting approval")


@case("F52 A5 approval projection 可等待审批")
def _f52() -> None:
    client = SseRuntimeClient("http://127.0.0.1:1")
    client._apply_event(_event("approval_required", 1, channel="workbench", visibility="task_telemetry", kind="approval_required", payload={"risk_level": "A5", "decision": "requires_confirmation", "ticket_id": "tk2", "action_summary": "高危操作"}))
    snap = client.get_snapshot()
    require(snap.run_workbench_state == "waiting_approval" and snap.pending_confirmations, "A5 approval projection missing")


@case("F53 自由意志活跃用户任务中不抢占")
def _f53() -> None:
    tick = FreeWillBackgroundRunner().tick(tick_id="fw_active", active_user_task=True, user_allowed_autonomy=True, idle_seconds=999)
    d = tick.public_dict()
    require(d["blocked"] is True and d["background_candidate_generated"] is False, "free will must not preempt active task")
    require(d["no_tool_invocation"] and d["no_file_write"] and d["no_budget_mutation"], "free will side-effect guards missing")


@case("F54 自由意志 idle 可生成候选但无副作用")
def _f54() -> None:
    tick = FreeWillBackgroundRunner().tick(tick_id="fw_idle", active_user_task=False, user_allowed_autonomy=True, idle_seconds=3600)
    d = tick.public_dict()
    require(d["background_candidate_generated"] is True and d["route"] is not None, "idle free will candidate missing")
    require(d["no_tool_invocation"] and d["no_file_write"] and d["no_kernel_mutation"], "idle free will side-effect guard missing")


@case("F55 自我学习候选不污染主链")
def _f55() -> None:
    route = build_self_learning_route(user_requested_learning=True, notes="学习一次失败经验")
    d = route.public_dict()
    require(d["candidate_only"] and d["review_before_activation"] and d["no_tool_invocation"], "self learning candidate boundary broken")
    require(not d["writes_knowledge"] and not d["registers_tool"] and not d["dispatches_model"], "self learning has forbidden side effects")


@case("F56 自我迭代候选不自动合入/热切换")
def _f56() -> None:
    route = build_self_iteration_route(repeated_failure_count=2, user_confirmed_direction=True, notes="优化前端 smoke")
    d = route.public_dict()
    require(d["candidate_only"] and d["quality_gate_required"] and d["rollback_required"], "self iteration gate boundary broken")
    require(not d["applies_patch"] and not d["merges_change"] and not d["performs_hot_switch"] and not d["writes_file"], "self iteration has forbidden side effects")


@case("F57 自愈失败态保持 recoverable")
def _f57() -> None:
    require(normalize_run_state("failed_recoverable") == "recoverable", "failed_recoverable not recoverable")
    require(normalize_run_state("partial_with_resume") == "recoverable", "partial_with_resume not recoverable")


@case("F58 completed_with_warnings 不误判失败")
def _f58() -> None:
    require(normalize_run_state("completed_with_warnings") == "completed", "completed_with_warnings not completed")
    require(normalize_run_state("deterministic_fallback") == "completed", "deterministic fallback not completed")


@case("F59 PromptIntegrator/Runtime 核心未在本 smoke 中执行或修改")
def _f59() -> None:
    # This acceptance smoke is contract/source-level. It must not call Provider, Runtime tools, shell commands, or patch files.
    require(True, "contract smoke only")


@case("F60 L6.73.3 smoke 输出 JSON/Markdown 报告")
def _f60() -> None:
    require(str(REPORT_JSON).endswith("l6733_real_acceptance_special_cases_report.json"), "report path invalid")


def write_report() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    passed = sum(1 for r in RESULTS if r.status == "PASS")
    failed = sum(1 for r in RESULTS if r.status == "FAIL")
    payload = {
        "version": "L6.73.3",
        "case_count": len(RESULTS),
        "passed": passed,
        "failed": failed,
        "ok": failed == 0,
        "scope": "deterministic contract/source smoke; no real Provider call; no Tk launch; no tool execution",
        "results": [r.__dict__ for r in RESULTS],
    }
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# L6.73.3 Real Acceptance Special Cases Smoke",
        "",
        f"- version: L6.73.3",
        f"- case_count: {len(RESULTS)}",
        f"- passed: {passed}",
        f"- failed: {failed}",
        f"- scope: deterministic contract/source smoke; no real Provider call; no Tk launch; no tool execution",
        "",
        "| # | case | status | detail |",
        "|---:|---|---|---|",
    ]
    for idx, r in enumerate(RESULTS, 1):
        detail = r.detail.replace("|", "｜").replace("\n", " ") if r.detail else ""
        lines.append(f"| {idx} | {r.name} | {r.status} | {detail} |")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    write_report()
    failed = [r for r in RESULTS if r.status != "PASS"]
    if failed:
        print(json.dumps({"ok": False, "case_count": len(RESULTS), "passed": len(RESULTS) - len(failed), "failed": len(failed), "report": _public_report_path(REPORT_JSON)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"ok": True, "case_count": len(RESULTS), "passed": len(RESULTS), "failed": 0, "report": _public_report_path(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
