from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Iterable, List, Mapping, Optional
import hashlib
import re
import time

from linyuanzhe_frontend.version_info import FE_FULL_VERSION
from .provider_settings_contract import PROVIDER_SETTINGS_WRITE_CONTRACT_VERSION
from .action_guard import (
    ACTION_GUARD_CONTRACT_VERSION,
    ActionGuardCard,
    AuditReadonlyCard,
    RollbackReadonlyCard,
)
from .observability import (
    OBSERVABILITY_CONTRACT_VERSION,
    TraceRecord,
    TraceStats,
)
from .hook_bus import (
    HOOK_BUS_CONTRACT_VERSION,
    HookRecord,
    HookStats,
)
from .file_transfer import (
    FILE_TRANSFER_CONTRACT_VERSION,
    FileTransferPublicRecord,
)
from .workspace import (
    WORKSPACE_CONTRACT_VERSION,
    WorkspaceMount,
    WorkspacePolicyProjection,
    FileAuthorizationPublicRecord,
    DownloadHandoffRecord,
)
from .connectors import (
    CONNECTOR_REGISTRY_CONTRACT_VERSION,
    ConnectorRegistryProjection,
    ConnectorManifestProjection,
    ConnectorRegistrationPublicRecord,
)
from .session_manager import (
    SESSION_MANAGER_CONTRACT_VERSION,
    TaskSessionProjection,
    SessionManagerStats,
)
from .installer_rc import (
    INSTALLER_RC_CONTRACT_VERSION,
    InstallerManifestProjection,
    VersionSlotProjection,
    StartupSelfCheckRecord,
    CrashReportProjection,
    RepairActionRecord,
    summarize_checks,
)

from .run_workbench import (
    RUN_WORKBENCH_CONTRACT_VERSION,
    RunWorkbenchProjection,
    normalize_run_state,
    run_state_label,
)


SENSITIVE_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd|private[_-]?key)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)(mockkey_[A-Za-z0-9_\-]{8,})"),
    re.compile(r"(?i)(bearer\s+[A-Za-z0-9_\-.]+)"),
    re.compile(r"([A-Za-z]:\\[^\n\r\t]+)"),
    re.compile(r"(/(?:home|Users|mnt|var|etc)/[^\n\r\t]+)"),
]


def _redact_sensitive_text(value: Any) -> str:
    text = "" if value is None else str(value)
    for pattern in SENSITIVE_PATTERNS:
        text = pattern.sub("<redacted>", text)
    return text


def safe_text(value: Any, max_len: int = 260) -> str:
    """Return UI-safe single-line summary text.

    The frontend only displays sanitized projections. This helper is a final
    defensive layer against accidental raw secret/path leakage in mock or JSON
    report inputs. It is not a replacement for backend PublicProjection.
    """
    text = _redact_sensitive_text(value)
    text = text.replace("\r", " ").replace("\n", " ").strip()
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text


def safe_path_setting_value(value: Any, max_len: int = 520) -> str:
    """Return a Settings-form path value without display redaction.

    ``safe_text`` deliberately redacts local paths before text is rendered in
    general chat, reports, and diagnostic cards. Custom host access roots are a
    user-entered Settings value and must remain exact when moved between the UI,
    the write-only Runtime request, and local UI preferences. This helper only
    strips control characters, normalizes to one line, and caps length; logging
    and public reports must still use digest/redacted fields.
    """
    text = "" if value is None else str(value)
    text = text.replace("\r", " ").replace("\n", " ").strip().strip('"').strip("'")
    text = "".join(ch for ch in text if ch == "\t" or ord(ch) >= 32)
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text


CHAT_MESSAGE_DISPLAY_LIMIT = 32000
CHAT_USER_INPUT_LIMIT = 12000
CHAT_TRUNCATION_NOTICE = "\n\n[前端显示保护：内容超过 {limit} 字，已截断；如需完整长链产物，请要求临渊者导出为文件或查看交付附件。]"


def safe_chat_text(value: Any, max_len: int = CHAT_MESSAGE_DISPLAY_LIMIT) -> str:
    """Return sanitized chat text while preserving Markdown-significant lines.

    STEP31Q needs newlines for headings, lists, paragraphs and fenced code
    blocks.  This remains display-only sanitization: secrets, tokens and local
    paths are redacted before the Tk renderer sees the text.
    """
    text = _redact_sensitive_text(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    normalized: List[str] = []
    blank_count = 0
    for line in lines:
        if line.strip():
            blank_count = 0
            normalized.append(line)
        else:
            blank_count += 1
            if blank_count <= 2:
                normalized.append("")
    text = "\n".join(normalized).strip("\n")
    if len(text) > max_len:
        notice = CHAT_TRUNCATION_NOTICE.format(limit=max_len)
        keep = max(1, max_len - len(notice) - 1)
        return text[:keep].rstrip() + "…" + notice
    return text


def digest_text(value: Any, length: int = 16) -> str:
    data = ("" if value is None else str(value)).encode("utf-8", errors="ignore")
    return hashlib.sha256(data).hexdigest()[:length]


@dataclass
class ChatMessage:
    role: str
    label: str
    time: str
    text: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ChatMessage":
        return cls(
            role=safe_text(data.get("role", "assistant"), 32),
            label=safe_text(data.get("label", "临渊者"), 32),
            time=safe_text(data.get("time", "--:--:--"), 32),
            text=safe_chat_text(data.get("text", ""), CHAT_MESSAGE_DISPLAY_LIMIT),
        )


@dataclass
class StepSummary:
    name: str
    status: str
    risk_level: str = "A0"
    audit_ref: str = ""
    output_summary: str = ""

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "StepSummary":
        return cls(
            name=safe_text(data.get("name") or data.get("tool_name") or data.get("step_name"), 64),
            status=safe_text(data.get("status") or data.get("state") or "queued", 32),
            risk_level=safe_text(data.get("risk_level", "A0"), 16),
            audit_ref=safe_text(data.get("audit_ref", ""), 64),
            output_summary=safe_text(data.get("output_summary", ""), 180),
        )


@dataclass
class TaskSnapshotProjection:
    task_id: str = "mock-task"
    current_stage: str = "待同步"
    current_step: str = "等待 Planner 输出"
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    recovery_points: List[str] = field(default_factory=list)
    budget_state: str = "预算正常"
    tool_state: str = "工具未接线"
    waiting_user_confirmation: bool = False
    next_plan: str = "等待下一步计划"
    snapshot_ref: str = "TASKSNAPSHOT-MOCK"

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "TaskSnapshotProjection":
        return cls(
            task_id=safe_text(data.get("task_id", "mock-task"), 80),
            current_stage=safe_text(data.get("current_stage", "待同步"), 80),
            current_step=safe_text(data.get("current_step", "等待 Planner 输出"), 100),
            completed_steps=[safe_text(x, 80) for x in data.get("completed_steps", []) or []],
            failed_steps=[safe_text(x, 80) for x in data.get("failed_steps", []) or []],
            recovery_points=[safe_text(x, 80) for x in data.get("recovery_points", []) or []],
            budget_state=safe_text(data.get("budget_state", "预算正常"), 80),
            tool_state=safe_text(data.get("tool_state", "工具未接线"), 80),
            waiting_user_confirmation=bool(data.get("waiting_user_confirmation", False)),
            next_plan=safe_text(data.get("next_plan", "等待下一步计划"), 160),
            snapshot_ref=safe_text(data.get("snapshot_ref", "TASKSNAPSHOT-MOCK"), 80),
        )


@dataclass
class ConversationGuideRoute:
    intent_summary: str = "继续当前任务"
    missing_information: List[str] = field(default_factory=list)
    suggested_questions: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    risk_hint: str = "无新增风险"
    continue_hint: str = "可以继续下一步"
    can_enter_long_chain: bool = True

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ConversationGuideRoute":
        return cls(
            intent_summary=safe_text(data.get("intent_summary", "继续当前任务"), 140),
            missing_information=[safe_text(x, 100) for x in data.get("missing_information", []) or []],
            suggested_questions=[safe_text(x, 120) for x in data.get("suggested_questions", []) or []],
            recommended_actions=[safe_text(x, 100) for x in data.get("recommended_actions", []) or []],
            risk_hint=safe_text(data.get("risk_hint", "无新增风险"), 140),
            continue_hint=safe_text(data.get("continue_hint", "可以继续下一步"), 140),
            can_enter_long_chain=bool(data.get("can_enter_long_chain", True)),
        )


@dataclass
class FourPathStatusProjection:
    execution_status: str = "执行链：等待"
    memory_status: str = "记忆：摘要可用"
    affective_status: str = "情志：稳定"
    lifecycle_status: str = "生命周期：候选待机"
    planner_context_digest: str = "CTX-MOCK"
    hard_boundary_summary: str = "所有真实动作仍走 Runtime / Planner / ExecutionSpine"

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "FourPathStatusProjection":
        return cls(
            execution_status=safe_text(data.get("execution_status", "执行链：等待"), 140),
            memory_status=safe_text(data.get("memory_status", "记忆：摘要可用"), 140),
            affective_status=safe_text(data.get("affective_status", "情志：稳定"), 140),
            lifecycle_status=safe_text(data.get("lifecycle_status", "生命周期：候选待机"), 140),
            planner_context_digest=safe_text(data.get("planner_context_digest", "CTX-MOCK"), 80),
            hard_boundary_summary=safe_text(data.get("hard_boundary_summary", "所有真实动作仍走 Runtime / Planner / ExecutionSpine"), 180),
        )


@dataclass
class SelfIterationCandidate:
    candidate_id: str = "ITER-MOCK-0001"
    title: str = "自我迭代候选"
    source: str = "用户沟通需求"
    expected_change: str = "等待用户确认后进入 Planner"
    risk_level: str = "A3"
    rollback_plan: str = "生成回滚点后再执行"
    test_requirement: str = "需要回归测试"
    requires_user_confirmation: bool = True
    status: str = "pending_user_confirmation"

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "SelfIterationCandidate":
        return cls(
            candidate_id=safe_text(data.get("candidate_id", "ITER-MOCK-0001"), 80),
            title=safe_text(data.get("title", "自我迭代候选"), 120),
            source=safe_text(data.get("source", "用户沟通需求"), 120),
            expected_change=safe_text(data.get("expected_change", "等待用户确认后进入 Planner"), 180),
            risk_level=safe_text(data.get("risk_level", "A3"), 16),
            rollback_plan=safe_text(data.get("rollback_plan", "生成回滚点后再执行"), 160),
            test_requirement=safe_text(data.get("test_requirement", "需要回归测试"), 160),
            requires_user_confirmation=bool(data.get("requires_user_confirmation", True)),
            status=safe_text(data.get("status", "pending_user_confirmation"), 60),
        )


@dataclass
class SelfIterationFrontendProjection:
    panel_status: str = "ready"
    pending_count: int = 0
    last_updated: str = "当前"
    candidates: List[SelfIterationCandidate] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "SelfIterationFrontendProjection":
        candidates = [SelfIterationCandidate.from_mapping(item) for item in data.get("candidates", []) or []]
        return cls(
            panel_status=safe_text(data.get("panel_status", "ready"), 60),
            pending_count=int(data.get("pending_count", len(candidates)) or 0),
            last_updated=safe_text(data.get("last_updated", "当前"), 80),
            candidates=candidates,
        )


@dataclass
class RuntimeSnapshot:
    schema_version: str = "linyuanzhe.frontend.runtime_snapshot.v1"
    session_id: str = "mock-session"
    runtime_status: str = "运行中"
    model_provider: str = "DeepSeek-R1 32K"
    planner_mode: str = "契约驱动"
    tool_execution_mode: str = "runtime_governed"
    connection_status: str = "已连接（延迟 32ms）"

    # L6.51.1 bottom status bar contract. These nine fields are display-only
    # and must be derived from backend PublicProjection / Runtime status, not
    # from frontend execution decisions.
    provider_model: str = "deepseek-v4-pro"
    budget_pool: str = "main_task"
    budget_used_ratio: str = "18%"
    gate_status: str = "A1 allowed"
    audit_id: str = "EV-250515-0001"
    memory_mode: str = "read_only_projection"
    tools_allowed: int = 5
    latency_ms: int = 32

    # L6.54 smooth Agent UI render contract. These fields are display-only
    # telemetry for batching, virtual transcript, and event normalization.
    agent_ui_contract: str = "tiangong.l6_55.agent_ui_event.v1"
    stream_render_contract: str = "tiangong.l6_54.stream_smooth_render.v1"
    render_mode: str = "delta_merge_virtual_transcript"
    agent_ui_event_count: int = 0
    pending_event_buffer_count: int = 0
    pending_delta_chars: int = 0
    visible_message_count: int = 0
    hidden_message_count: int = 0
    stream_activity_label: str = ""
    stream_visual_state: str = "idle"

    # L6.62 Trace / Observability dashboard. Display-only projection from
    # Runtime SSE / Agent UI events; no frontend execution authority.
    observability_contract: str = OBSERVABILITY_CONTRACT_VERSION
    trace_enabled: bool = True
    trace_records: List[TraceRecord] = field(default_factory=list)
    trace_stats: Dict[str, Any] = field(default_factory=dict)
    trace_terminal_order_valid: bool = True
    trace_export_digest: str = ""

    # L6.63 deterministic HookBus. Display-only projection of local hook
    # decisions around outbound request envelopes and inbound Runtime events.
    hook_bus_contract: str = HOOK_BUS_CONTRACT_VERSION
    hook_enabled: bool = True
    hook_records: List[HookRecord] = field(default_factory=list)
    hook_stats: Dict[str, Any] = field(default_factory=dict)
    hook_last_blocker: str = ""
    hook_export_digest: str = ""

    # L6.64 file transfer frontend contract. Display-only projection of sanitized
    # transfer requests; raw paths and file contents never enter reports.
    file_transfer_contract: str = FILE_TRANSFER_CONTRACT_VERSION
    file_transfer_enabled: bool = True
    file_transfer_state: str = "idle"
    file_transfer_records: List[FileTransferPublicRecord] = field(default_factory=list)
    file_transfer_last_message: str = "等待文件传输请求"

    # L6.65 Agent Workspace / sandbox and file authorization. Display-only
    # policy projection; file authorization and download handoff remain Runtime-governed.
    workspace_contract: str = WORKSPACE_CONTRACT_VERSION
    workspace_enabled: bool = True
    workspace_state: str = "ready"
    workspace_policy: WorkspacePolicyProjection = field(default_factory=WorkspacePolicyProjection)
    workspace_mounts: List[WorkspaceMount] = field(default_factory=list)
    file_authorization_records: List[FileAuthorizationPublicRecord] = field(default_factory=list)
    download_handoff_records: List[DownloadHandoffRecord] = field(default_factory=list)
    workspace_last_message: str = "Agent Workspace 等待 Runtime 授权投影"

    # L6.66 MCP / connector registry. Display-only registry projection;
    # registration/quarantine remain Runtime-governed request envelopes.
    connector_registry_contract: str = CONNECTOR_REGISTRY_CONTRACT_VERSION
    connector_registry_enabled: bool = True
    connector_registry_state: str = "ready"
    connector_registry_projection: ConnectorRegistryProjection = field(default_factory=ConnectorRegistryProjection)
    connector_manifests: List[ConnectorManifestProjection] = field(default_factory=list)
    connector_registration_records: List[ConnectorRegistrationPublicRecord] = field(default_factory=list)
    connector_last_message: str = "MCP / 连接器注册表等待 Runtime 投影"

    # L6.67 multi-task Session Manager. Display-only task tower projection;
    # resume/search/archive are Runtime-governed request envelopes only.
    session_manager_contract: str = SESSION_MANAGER_CONTRACT_VERSION
    session_manager_enabled: bool = True
    session_manager_state: str = "ready"
    task_sessions: List[TaskSessionProjection] = field(default_factory=list)
    session_stats: Dict[str, Any] = field(default_factory=dict)
    session_last_message: str = "任务 Session 管理器等待 Runtime 投影"
    session_search_query: str = ""
    session_filtered_count: int = 0

    # L6.68 installer RC pre-stage. Display-only installer/update/recovery
    # projections; frontend may not build installers, apply updates, restore
    # rollback slots, upload crash reports, or mutate Runtime core files.
    installer_rc_contract: str = INSTALLER_RC_CONTRACT_VERSION
    installer_rc_enabled: bool = True
    installer_stage: str = "rc_preinstall"
    installer_manifest: InstallerManifestProjection = field(default_factory=InstallerManifestProjection)
    version_slots: List[VersionSlotProjection] = field(default_factory=list)
    startup_self_checks: List[StartupSelfCheckRecord] = field(default_factory=list)
    crash_report_records: List[CrashReportProjection] = field(default_factory=list)
    repair_action_records: List[RepairActionRecord] = field(default_factory=list)
    installer_last_message: str = "安装器 RC 前置结构等待自检"
    startup_self_check_state: str = "pending"
    update_channel: str = "internal_rc"

    # L6.55 QualityGate action guard / evidence cards. Display-only cards: the
    # frontend may submit a request envelope to Runtime, but may not execute,
    # bypass Gate, write Audit, or apply Rollback locally.
    action_guard_contract: str = ACTION_GUARD_CONTRACT_VERSION
    action_guard_cards: List[ActionGuardCard] = field(default_factory=list)
    audit_readonly_cards: List[AuditReadonlyCard] = field(default_factory=list)
    rollback_readonly_cards: List[RollbackReadonlyCard] = field(default_factory=list)
    last_confirmation_request: Dict[str, Any] = field(default_factory=dict)
    confirmation_request_state: str = "idle"

    # L6.57 Provider settings write acknowledgement. Display-only state: the
    # frontend may submit write-only credentials to Runtime, but it must clear
    # raw inputs immediately and only display configured flags/digests/errors.
    provider_settings_contract: str = PROVIDER_SETTINGS_WRITE_CONTRACT_VERSION
    provider_config_state: str = "idle"
    provider_config_message: str = "未提交 Runtime Provider 设置"
    provider_config_error_code: str = ""
    provider_config_audit_id: str = ""
    provider_api_key_configured: bool = False
    provider_api_key_digest: str = ""
    provider_base_url_configured: bool = False
    provider_base_url_digest: str = ""
    last_provider_check_state: str = "not_tested"
    last_provider_error_code: str = ""
    last_provider_error_message: str = ""
    last_provider_next_action: str = "发送一条短消息完成真实链路联调"

    # L6.53 streaming/control display contract. These are UI state markers only;
    # they do not authorize frontend-side execution, stop, reset, rollback, or memory writes.
    stream_state: str = "idle"
    reconnect_attempts: int = 0
    last_event_seq: int = 0
    terminal_order_valid: bool = True
    control_state: str = "ready"
    active_run_id: str = ""
    active_task_id: str = ""

    # L6.72.27 Desktop Run Workbench. Display-only tamockkey_console state;
    # frontend may reconnect, stop, and submit approvals through Runtime envelopes,
    # but it still never executes tools or applies decisions locally.
    run_workbench_contract: str = RUN_WORKBENCH_CONTRACT_VERSION
    run_workbench: RunWorkbenchProjection = field(default_factory=RunWorkbenchProjection)
    run_workbench_state: str = "idle"
    run_status_label: str = "待机"
    frontend_work_mode: str = "work"
    current_tool_name: str = ""
    current_tool_status: str = ""
    waiting_approval_ticket_id: str = ""
    run_heartbeat_count: int = 0
    run_heartbeat_age_ms: int = 0
    run_last_event: str = ""
    run_last_event_at: str = ""
    run_reconnect_available: bool = False
    run_resume_available: bool = False
    run_stop_available: bool = False
    run_diagnostic_summary: str = ""
    frontend_executes_tools: bool = False

    current_task_status: str = "RUNNING"
    progress_percent: int = 67
    plan_id: str = "plan_20250515_p0_integration"
    current_stage: str = "接口联调与验证"
    eta: str = "2025-05-15 13:30"

    success_count: int = 8
    blocked_count: int = 2
    pending_confirmation_count: int = 0

    execution_stage: str = "接口联调中"
    execution_steps: List[StepSummary] = field(default_factory=list)

    quality_decision: str = "CONDITIONAL"
    quality_allow_continue: bool = True
    quality_allow_package: bool = False
    quality_gate_status: str = "warning"
    blocking_reasons: List[str] = field(default_factory=list)

    audit_count: int = 128
    evidence_ref: str = "EV-250515-0001"

    memory_sanitized_summary: str = "P0 系统接入上下文已读取安全摘要；未展示原始记忆正文。"
    memory_digest: str = "mock_digest_0001"
    memory_evidence_ref: str = "memory_ev_0001"

    recovery_ticket_id: str = ""
    recovery_failure_count: int = 0
    recovery_resume_plan_count: int = 0
    recovery_next_actions: List[str] = field(default_factory=list)
    recovery_requires_human_confirmation: bool = False

    chat_messages: List[ChatMessage] = field(default_factory=list)
    pending_confirmations: List[Dict[str, Any]] = field(default_factory=list)
    delivery_artifacts: List[Dict[str, Any]] = field(default_factory=list)
    source_kind: str = "mock"

    task_snapshot: TaskSnapshotProjection = field(default_factory=TaskSnapshotProjection)
    conversation_guide: ConversationGuideRoute = field(default_factory=ConversationGuideRoute)
    four_path_status: FourPathStatusProjection = field(default_factory=FourPathStatusProjection)
    self_iteration_projection: SelfIterationFrontendProjection = field(default_factory=SelfIterationFrontendProjection)

    def __post_init__(self) -> None:
        is_mock_source = safe_text(getattr(self, "source_kind", "mock"), 80) in {"mock", "mock_file", "frontend_mock", "demo", "mock_data"}
        if is_mock_source and not self.execution_steps:
            self.execution_steps = [
                StepSummary("接口对接", "succeeded", "A2", "audit_mock_001", "接口对接完成"),
                StepSummary("权限验证", "succeeded", "A2", "audit_mock_002", "权限验证完成"),
                StepSummary("数据同步", "running", "A2", "audit_mock_003", "数据同步进行中"),
            ]
        if is_mock_source and not self.chat_messages:
            self.chat_messages = [
                ChatMessage("user", "你", "10:24:18", "请继续推进 P0 系统接入。"),
                ChatMessage(
                    "assistant",
                    "临渊者",
                    "10:24:26",
                    "已推进 P0 系统接入工作。\n接口对接与权限验证已完成，数据同步服务已启动。\n下一步将进行订单推送与回执验证。",
                ),
            ]
        if self.visible_message_count <= 0:
            self.visible_message_count = len(self.chat_messages)
        self.run_workbench_state = normalize_run_state(self.run_workbench_state or getattr(self.run_workbench, "state", "idle"))
        if not self.run_status_label or (self.run_status_label == "待机" and self.run_workbench_state != "idle"):
            self.run_status_label = run_state_label(self.run_workbench_state)
        self.run_status_label = safe_text(self.run_status_label, 40)
        object.__setattr__(self.run_workbench, "state", self.run_workbench_state)
        object.__setattr__(self.run_workbench, "label", self.run_status_label)
        object.__setattr__(self.run_workbench, "run_id", self.active_run_id or self.run_workbench.run_id)
        object.__setattr__(self.run_workbench, "task_id", self.active_task_id or self.run_workbench.task_id)
        if is_mock_source and not self.trace_records:
            self.trace_records = [
                TraceRecord(seq=1, event_type="run_started", source_event="run_started", category="run", phase="mock_ready", status="ready", message="Mock 运行观测投影已初始化"),
                TraceRecord(seq=2, event_type="runtime_state", source_event="runtime_state", category="runtime", phase=self.current_stage, status=self.current_task_status, latency_ms=self.latency_ms, message="Runtime 状态投影"),
                TraceRecord(seq=3, event_type="quality_gate_required", source_event="quality_gate", category="quality_gate", phase=self.gate_status, decision=self.quality_decision, audit_ref=self.audit_id, message="QualityGate 只读投影"),
            ]
        if not self.trace_stats:
            self.trace_stats = TraceStats.from_records(self.trace_records).to_dict()
        self.trace_terminal_order_valid = bool(self.trace_stats.get("terminal_order_valid", True))
        self.trace_export_digest = digest_text(self.trace_stats, 16)
        if not self.hook_records:
            self.hook_records = [
                HookRecord(seq=1, stage="pre_event_apply", rule_id="a5_cannot_be_allowed", verdict="allow", severity="info", reason="Mock HookBus baseline ready", source_event="quality_gate"),
                HookRecord(seq=2, stage="pre_finalize", rule_id="finalize_trace", verdict="allow", severity="info", reason="Mock closeout checks ready"),
            ]
        if not self.hook_stats:
            self.hook_stats = HookStats.from_records(self.hook_records).to_dict()
        self.hook_last_blocker = safe_text(self.hook_stats.get("last_blocker", ""), 220)
        self.hook_export_digest = digest_text(self.hook_stats, 16)
        if is_mock_source and not self.file_transfer_records:
            self.file_transfer_records = [
                FileTransferPublicRecord(
                    transfer_id="FT-MOCK-READY",
                    file_name="等待选择文件",
                    size_bytes=0,
                    status="ready",
                    message="文件传输入口已接入；真实文件只经 Runtime / TiangongWangguan 授权链路。",
                )
            ]
        if is_mock_source and not self.workspace_mounts:
            self.workspace_mounts = [
                WorkspaceMount(
                    name="agent_workspace",
                    scope="temporary_handoff",
                    mode="read",
                    path_digest="WORKSPACE-MOCK",
                    writable=False,
                    runtime_owned=True,
                    expires_hint="per_run",
                )
            ]
        if not self.workspace_policy.mounts:
            object.__setattr__(self.workspace_policy, "mounts", self.workspace_mounts[:])
        if is_mock_source and not self.file_authorization_records:
            self.file_authorization_records = [
                FileAuthorizationPublicRecord(
                    authorization_id="AUTH-MOCK-READY",
                    file_name="等待授权文件",
                    mode="read",
                    scope="user_selected_file",
                    status="ready",
                    message="文件授权边界已接入；真实授权只由 Runtime / QualityGate / TiangongWangguan 裁决。",
                )
            ]
        if is_mock_source and not self.download_handoff_records:
            self.download_handoff_records = [
                DownloadHandoffRecord(
                    artifact_id_digest="DL-MOCK-READY",
                    file_name="等待 Runtime 下载中转回执",
                    status="ready",
                    message="前端只展示下载中转回执，不显示原始下载 token。",
                )
            ]
        if is_mock_source and not self.connector_manifests:
            self.connector_manifests = [
                ConnectorManifestProjection(
                    connector_id_digest="CONN-MOCK-READY",
                    display_name="等待注册 MCP / 连接器",
                    kind="mcp_server",
                    version="0.0.0",
                    trust_level="unknown",
                    default_mode="disabled",
                    status="ready",
                    capabilities=["registry_projection"],
                    manifest_digest="MANIFEST-MOCK",
                    read_only_default=True,
                    quality_gate_required=True,
                    workspace_authorization_required=True,
                    runtime_authority_required=True,
                )
            ]
        if is_mock_source and not self.connector_registration_records:
            self.connector_registration_records = [
                ConnectorRegistrationPublicRecord(
                    request_id="CONN-REQ-MOCK-READY",
                    display_name="等待连接器注册请求",
                    kind="mcp_server",
                    status="ready",
                    message="连接器注册表前置治理已接入；开放市场安装、前端执行和前端密钥存储均禁止。",
                    manifest_digest="MANIFEST-MOCK",
                )
            ]
        if self.connector_registry_projection.connector_count <= 0 and self.connector_manifests:
            object.__setattr__(self.connector_registry_projection, "connector_count", len(self.connector_manifests))
            object.__setattr__(self.connector_registry_projection, "read_only_count", sum(1 for item in self.connector_manifests if item.read_only_default))
            object.__setattr__(self.connector_registry_projection, "quarantined_count", sum(1 for item in self.connector_manifests if item.quarantined))

        if is_mock_source and not self.task_sessions:
            # STEP31E: production desktop shells must not inject recoverable demo
            # sessions. A single active projection is enough for mock/demo mode;
            # SESS-MOCK-* rows caused false resume requests in the task tower.
            active_title = self.task_snapshot.current_stage or self.current_stage or "当前任务"
            self.task_sessions = [
                TaskSessionProjection(
                    session_id_digest=digest_text(self.session_id or "active-session", 16),
                    title=safe_text(active_title, 120),
                    status="running" if self.current_task_status in {"RUNNING", "STREAMING"} else safe_text(self.current_task_status, 40).lower(),
                    current_stage=safe_text(self.current_stage, 140),
                    progress_percent=self.progress_percent,
                    waiting_confirmation=bool(self.task_snapshot.waiting_user_confirmation or self.pending_confirmation_count > 0),
                    blocked=bool(self.blocked_count > 0 and not self.quality_allow_continue),
                    recoverable=bool(self.recovery_resume_plan_count > 0 or self.recovery_ticket_id),
                    active=True,
                    last_updated="当前",
                    run_id_digest=digest_text(self.active_run_id or self.session_id, 16),
                    task_id_digest=digest_text(self.active_task_id or self.task_snapshot.task_id, 16),
                    audit_id=self.audit_id,
                    tags=["active", "runtime_projection"],
                    message="当前任务由 Runtime 投影；前端只显示和提交请求。",
                )
            ]
        if self.task_sessions:
            self.task_sessions = [
                item for item in self.task_sessions
                if not safe_text(getattr(item, "session_id_digest", ""), 80).upper().startswith("SESS-MOCK")
            ]
        if not self.session_stats:
            self.session_stats = SessionManagerStats.from_sessions(self.task_sessions).to_dict()
        if self.session_filtered_count <= 0:
            self.session_filtered_count = len(self.task_sessions)

        if is_mock_source and not self.version_slots:
            self.version_slots = [
                VersionSlotProjection(
                    slot_name="active",
                    version_label="FE01 STEP29 / L6.68",
                    state="active",
                    path_digest="SLOT-ACTIVE-MOCK",
                    package_sha256_digest="等待发布包 sha256",
                    last_verified="启动自检待运行",
                    rollback_capable=True,
                    message="当前工程包活动槽；真实安装器尚未生成。",
                ),
                VersionSlotProjection(
                    slot_name="rollback",
                    version_label=FE_FULL_VERSION,
                    state="rollback",
                    path_digest="SLOT-ROLLBACK-MOCK",
                    package_sha256_digest="上一基线 digest 待 Runtime/Installer 填充",
                    last_verified="待离线修复脚本确认",
                    rollback_capable=True,
                    message="回滚槽仅为前置结构，不由前端应用。",
                ),
                VersionSlotProjection(
                    slot_name="candidate",
                    version_label="下一候选更新",
                    state="candidate",
                    path_digest="SLOT-CANDIDATE-MOCK",
                    last_verified="未下载",
                    rollback_capable=False,
                    message="更新器骨架预留；当前禁止自动下载/自动应用。",
                ),
            ]
        if is_mock_source and not self.startup_self_checks:
            self.startup_self_checks = [
                StartupSelfCheckRecord(check_id="backend_layout", name="后端目录与 run_agent 入口", status="pending", message="等待 startup_self_check_l668.py 校验"),
                StartupSelfCheckRecord(check_id="frontend_layout", name="前端桌面端与 RuntimeClient", status="pending", message="等待 startup_self_check_l668.py 校验"),
                StartupSelfCheckRecord(check_id="launcher_layout", name="统一启动器与预检脚本", status="pending", message="等待 startup_self_check_l668.py 校验"),
                StartupSelfCheckRecord(check_id="reports_writable", name="报告目录可写", status="pending", message="等待 startup_self_check_l668.py 校验"),
            ]
        if is_mock_source and not self.crash_report_records:
            self.crash_report_records = [
                CrashReportProjection(
                    report_id_digest="CRASH-MOCK-EMPTY",
                    status="empty",
                    crash_count=0,
                    safe_summary="暂无崩溃报告；崩溃摘要默认本地保存。",
                    local_only=True,
                    upload_allowed=False,
                )
            ]
        if is_mock_source and not self.repair_action_records:
            self.repair_action_records = [
                RepairActionRecord(action_id="startup_self_check", title="启动自检", status="available", message="运行 installer/startup/startup_self_check_l668.py。"),
                RepairActionRecord(action_id="offline_repair", title="离线修复预检", status="available", message="运行 installer/recovery/offline_repair_l668.py，默认 dry-run。"),
                RepairActionRecord(action_id="rollback_plan", title="回滚槽恢复计划", status="available", message="运行 installer/recovery/rollback_slot_restore_l668.py，仅生成计划。"),
            ]
        if not self.installer_manifest.slots and self.version_slots:
            object.__setattr__(self.installer_manifest, "slots", self.version_slots[:])
        if not self.installer_manifest.startup_checks and self.startup_self_checks:
            object.__setattr__(self.installer_manifest, "startup_checks", self.startup_self_checks[:])
        if not self.installer_manifest.crash_reports and self.crash_report_records:
            object.__setattr__(self.installer_manifest, "crash_reports", self.crash_report_records[:])
        if not self.installer_manifest.repair_actions and self.repair_action_records:
            object.__setattr__(self.installer_manifest, "repair_actions", self.repair_action_records[:])
        self.installer_stage = safe_text(self.installer_manifest.package_stage or self.installer_stage, 80)
        self.update_channel = safe_text(self.installer_manifest.update_channel or self.update_channel, 80)
        self.startup_self_check_state = safe_text(self.installer_manifest.startup_self_check_state or self.startup_self_check_state, 80)
        if not self.installer_last_message:
            check_summary = summarize_checks(self.startup_self_checks)
            self.installer_last_message = f"安装器 RC 前置：slots={len(self.version_slots)} checks={check_summary.get('total', 0)}；未生成最终安装包。"

        if not self.task_snapshot.completed_steps and self.execution_steps:
            self.task_snapshot.completed_steps = [step.name for step in self.execution_steps if step.status == "succeeded"][:5]
            self.task_snapshot.failed_steps = [step.name for step in self.execution_steps if step.status in {"failed", "blocked", "timeout"}][:5]
            self.task_snapshot.current_stage = self.current_stage
            self.task_snapshot.current_step = next((step.name for step in self.execution_steps if step.status in {"running", "queued", "confirmation_required"}), self.execution_stage)
            self.task_snapshot.waiting_user_confirmation = self.pending_confirmation_count > 0
            self.task_snapshot.next_plan = self.execution_stage
        if not self.conversation_guide.recommended_actions:
            self.conversation_guide.recommended_actions = ["继续下一步", "查看任务快照", "查看执行详情"]
        if is_mock_source and not self.self_iteration_projection.candidates:
            self.self_iteration_projection.candidates = [
                SelfIterationCandidate(
                    candidate_id="ITER-FE01-0001",
                    title="补齐前端任务快照与对话引导",
                    source="用户沟通需求",
                    expected_change="接入 TaskSnapshotProjection / ConversationGuideRoute / 自我迭代区",
                    risk_level="A3",
                    rollback_plan="保留 FE.01 STEP10B 基线包，可回滚",
                    test_requirement="运行 compileall、smoke_test_frontend、validate_demo_package",
                    requires_user_confirmation=True,
                    status="pending_user_confirmation",
                )
            ]
            self.self_iteration_projection.pending_count = 1

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "RuntimeSnapshot":
        steps = [StepSummary.from_mapping(item) for item in data.get("execution_steps", []) or []]
        messages = [ChatMessage.from_mapping(item) for item in data.get("chat_messages", []) or []]
        blocking = [safe_text(x, 120) for x in data.get("blocking_reasons", []) or []]
        recovery_actions = [safe_text(x, 160) for x in data.get("recovery_next_actions", []) or []]
        action_guard_cards = [
            item if isinstance(item, ActionGuardCard) else ActionGuardCard.from_quality_gate_payload(item)
            for item in data.get("action_guard_cards", []) or []
            if isinstance(item, (Mapping, ActionGuardCard))
        ]
        trace_records = [
            item if isinstance(item, TraceRecord) else TraceRecord.from_mapping(item)
            for item in data.get("trace_records", []) or []
            if isinstance(item, (Mapping, TraceRecord))
        ]
        trace_stats_raw = data.get("trace_stats", {}) or {}
        trace_stats = dict(trace_stats_raw) if isinstance(trace_stats_raw, Mapping) else {}
        if trace_records and not trace_stats:
            trace_stats = TraceStats.from_records(trace_records).to_dict()
        hook_records = [
            item if isinstance(item, HookRecord) else HookRecord.from_mapping(item)
            for item in data.get("hook_records", []) or []
            if isinstance(item, (Mapping, HookRecord))
        ]
        hook_stats_raw = data.get("hook_stats", {}) or {}
        hook_stats = dict(hook_stats_raw) if isinstance(hook_stats_raw, Mapping) else {}
        if hook_records and not hook_stats:
            hook_stats = HookStats.from_records(hook_records).to_dict()
        file_transfer_records = [
            item if isinstance(item, FileTransferPublicRecord) else FileTransferPublicRecord.from_mapping(item)
            for item in data.get("file_transfer_records", []) or []
            if isinstance(item, (Mapping, FileTransferPublicRecord))
        ]
        workspace_mounts = [
            item if isinstance(item, WorkspaceMount) else WorkspaceMount.from_mapping(item)
            for item in data.get("workspace_mounts", []) or []
            if isinstance(item, (Mapping, WorkspaceMount))
        ]
        file_authorization_records = [
            item if isinstance(item, FileAuthorizationPublicRecord) else FileAuthorizationPublicRecord.from_mapping(item)
            for item in data.get("file_authorization_records", []) or []
            if isinstance(item, (Mapping, FileAuthorizationPublicRecord))
        ]
        download_handoff_records = [
            item if isinstance(item, DownloadHandoffRecord) else DownloadHandoffRecord.from_mapping(item)
            for item in data.get("download_handoff_records", []) or []
            if isinstance(item, (Mapping, DownloadHandoffRecord))
        ]
        connector_manifests = [
            item if isinstance(item, ConnectorManifestProjection) else ConnectorManifestProjection.from_mapping(item)
            for item in data.get("connector_manifests", []) or []
            if isinstance(item, (Mapping, ConnectorManifestProjection))
        ]
        connector_registration_records = [
            item if isinstance(item, ConnectorRegistrationPublicRecord) else ConnectorRegistrationPublicRecord.from_mapping(item)
            for item in data.get("connector_registration_records", []) or []
            if isinstance(item, (Mapping, ConnectorRegistrationPublicRecord))
        ]
        connector_registry_projection = ConnectorRegistryProjection.from_mapping(data.get("connector_registry_projection", {}) or {})
        task_sessions = [
            item if isinstance(item, TaskSessionProjection) else TaskSessionProjection.from_mapping(item)
            for item in data.get("task_sessions", data.get("sessions", [])) or []
            if isinstance(item, (Mapping, TaskSessionProjection))
        ]
        session_stats_raw = data.get("session_stats", {}) or {}
        session_stats = dict(session_stats_raw) if isinstance(session_stats_raw, Mapping) else {}
        if task_sessions and not session_stats:
            session_stats = SessionManagerStats.from_sessions(task_sessions).to_dict()
        installer_manifest = InstallerManifestProjection.from_mapping(data.get("installer_manifest", {}) or {})
        version_slots = [
            item if isinstance(item, VersionSlotProjection) else VersionSlotProjection.from_mapping(item)
            for item in data.get("version_slots", data.get("installer_version_slots", [])) or []
            if isinstance(item, (Mapping, VersionSlotProjection))
        ]
        startup_self_checks = [
            item if isinstance(item, StartupSelfCheckRecord) else StartupSelfCheckRecord.from_mapping(item)
            for item in data.get("startup_self_checks", data.get("installer_startup_checks", [])) or []
            if isinstance(item, (Mapping, StartupSelfCheckRecord))
        ]
        crash_report_records = [
            item if isinstance(item, CrashReportProjection) else CrashReportProjection.from_mapping(item)
            for item in data.get("crash_report_records", data.get("crash_reports", [])) or []
            if isinstance(item, (Mapping, CrashReportProjection))
        ]
        repair_action_records = [
            item if isinstance(item, RepairActionRecord) else RepairActionRecord.from_mapping(item)
            for item in data.get("repair_action_records", data.get("repair_actions", [])) or []
            if isinstance(item, (Mapping, RepairActionRecord))
        ]
        if not version_slots and installer_manifest.slots:
            version_slots = list(installer_manifest.slots)
        if not startup_self_checks and installer_manifest.startup_checks:
            startup_self_checks = list(installer_manifest.startup_checks)
        if not crash_report_records and installer_manifest.crash_reports:
            crash_report_records = list(installer_manifest.crash_reports)
        if not repair_action_records and installer_manifest.repair_actions:
            repair_action_records = list(installer_manifest.repair_actions)
        workspace_policy = WorkspacePolicyProjection.from_mapping(data.get("workspace_policy", {}) or {})
        audit_readonly_cards = [
            item if isinstance(item, AuditReadonlyCard) else AuditReadonlyCard.from_payload(item)
            for item in data.get("audit_readonly_cards", []) or []
            if isinstance(item, (Mapping, AuditReadonlyCard))
        ]
        rollback_readonly_cards = [
            item if isinstance(item, RollbackReadonlyCard) else RollbackReadonlyCard.from_payload(item)
            for item in data.get("rollback_readonly_cards", []) or []
            if isinstance(item, (Mapping, RollbackReadonlyCard))
        ]
        run_workbench = RunWorkbenchProjection.from_mapping(data.get("run_workbench", {}) or {
            "state": data.get("run_workbench_state", data.get("stream_state", "idle")),
            "run_id": data.get("active_run_id", data.get("session_id", "")),
            "task_id": data.get("active_task_id", ""),
            "frontend_work_mode": data.get("frontend_work_mode", "work"),
            "current_tool_name": data.get("current_tool_name", ""),
            "current_tool_status": data.get("current_tool_status", ""),
            "waiting_ticket_id": data.get("waiting_approval_ticket_id", ""),
            "heartbeat_count": data.get("run_heartbeat_count", 0),
            "heartbeat_age_ms": data.get("run_heartbeat_age_ms", 0),
            "last_event": data.get("run_last_event", ""),
            "last_event_at": data.get("run_last_event_at", ""),
            "diagnostic_summary": data.get("run_diagnostic_summary", ""),
        })
        return cls(
            schema_version=safe_text(data.get("schema_version", "linyuanzhe.frontend.runtime_snapshot.v1"), 80),
            session_id=safe_text(data.get("session_id", "mock-session"), 80),
            runtime_status=safe_text(data.get("runtime_status", "运行中"), 40),
            model_provider=safe_text(data.get("model_provider", "DeepSeek-R1 32K"), 80),
            planner_mode=safe_text(data.get("planner_mode", "契约驱动"), 80),
            tool_execution_mode=safe_text(data.get("tool_execution_mode", "runtime_governed"), 80),
            connection_status=safe_text(data.get("connection_status", "已连接（延迟 32ms）"), 80),
            provider_model=safe_text(data.get("provider_model", data.get("model_provider", "deepseek-v4-pro")), 80),
            budget_pool=safe_text(data.get("budget_pool", "main_task"), 80),
            budget_used_ratio=safe_text(data.get("budget_used_ratio", "18%"), 32),
            gate_status=safe_text(data.get("gate_status", data.get("quality_gate_status", "A1 allowed")), 64),
            audit_id=safe_text(data.get("audit_id", data.get("evidence_ref", "EV-250515-0001")), 80),
            memory_mode=safe_text(data.get("memory_mode", "read_only_projection"), 80),
            tools_allowed=int(data.get("tools_allowed", 5) or 0),
            latency_ms=int(data.get("latency_ms", 32) or 0),
            agent_ui_contract=safe_text(data.get("agent_ui_contract", "tiangong.l6_55.agent_ui_event.v1"), 100),
            stream_render_contract=safe_text(data.get("stream_render_contract", "tiangong.l6_54.stream_smooth_render.v1"), 100),
            render_mode=safe_text(data.get("render_mode", "delta_merge_virtual_transcript"), 80),
            agent_ui_event_count=int(data.get("agent_ui_event_count", 0) or 0),
            pending_event_buffer_count=int(data.get("pending_event_buffer_count", 0) or 0),
            pending_delta_chars=int(data.get("pending_delta_chars", 0) or 0),
            visible_message_count=int(data.get("visible_message_count", 0) or 0),
            hidden_message_count=int(data.get("hidden_message_count", 0) or 0),
            stream_activity_label=safe_text(data.get("stream_activity_label", ""), 80),
            stream_visual_state=safe_text(data.get("stream_visual_state", data.get("stream_state", "idle")), 40),
            observability_contract=safe_text(data.get("observability_contract", OBSERVABILITY_CONTRACT_VERSION), 100),
            trace_enabled=bool(data.get("trace_enabled", True)),
            trace_records=trace_records,
            trace_stats=trace_stats,
            trace_terminal_order_valid=bool(data.get("trace_terminal_order_valid", trace_stats.get("terminal_order_valid", True))),
            trace_export_digest=safe_text(data.get("trace_export_digest", ""), 32),
            hook_bus_contract=safe_text(data.get("hook_bus_contract", HOOK_BUS_CONTRACT_VERSION), 100),
            hook_enabled=bool(data.get("hook_enabled", True)),
            hook_records=hook_records,
            hook_stats=hook_stats,
            hook_last_blocker=safe_text(data.get("hook_last_blocker", hook_stats.get("last_blocker", "")), 220),
            hook_export_digest=safe_text(data.get("hook_export_digest", ""), 32),
            file_transfer_contract=safe_text(data.get("file_transfer_contract", FILE_TRANSFER_CONTRACT_VERSION), 100),
            file_transfer_enabled=bool(data.get("file_transfer_enabled", True)),
            file_transfer_state=safe_text(data.get("file_transfer_state", "idle"), 80),
            file_transfer_records=file_transfer_records,
            file_transfer_last_message=safe_text(data.get("file_transfer_last_message", "等待文件传输请求"), 220),
            workspace_contract=safe_text(data.get("workspace_contract", WORKSPACE_CONTRACT_VERSION), 100),
            workspace_enabled=bool(data.get("workspace_enabled", True)),
            workspace_state=safe_text(data.get("workspace_state", "ready"), 80),
            workspace_policy=workspace_policy,
            workspace_mounts=workspace_mounts,
            file_authorization_records=file_authorization_records,
            download_handoff_records=download_handoff_records,
            workspace_last_message=safe_text(data.get("workspace_last_message", "Agent Workspace 等待 Runtime 授权投影"), 220),
            connector_registry_contract=safe_text(data.get("connector_registry_contract", CONNECTOR_REGISTRY_CONTRACT_VERSION), 100),
            connector_registry_enabled=bool(data.get("connector_registry_enabled", True)),
            connector_registry_state=safe_text(data.get("connector_registry_state", "ready"), 80),
            connector_registry_projection=connector_registry_projection,
            connector_manifests=connector_manifests,
            connector_registration_records=connector_registration_records,
            connector_last_message=safe_text(data.get("connector_last_message", "MCP / 连接器注册表等待 Runtime 投影"), 220),
            session_manager_contract=safe_text(data.get("session_manager_contract", SESSION_MANAGER_CONTRACT_VERSION), 100),
            session_manager_enabled=bool(data.get("session_manager_enabled", True)),
            session_manager_state=safe_text(data.get("session_manager_state", "ready"), 80),
            task_sessions=task_sessions,
            session_stats=session_stats,
            session_last_message=safe_text(data.get("session_last_message", "任务 Session 管理器等待 Runtime 投影"), 220),
            session_search_query=safe_text(data.get("session_search_query", ""), 120),
            session_filtered_count=int(data.get("session_filtered_count", len(task_sessions)) or 0),
            installer_rc_contract=safe_text(data.get("installer_rc_contract", INSTALLER_RC_CONTRACT_VERSION), 100),
            installer_rc_enabled=bool(data.get("installer_rc_enabled", True)),
            installer_stage=safe_text(data.get("installer_stage", installer_manifest.package_stage or "rc_preinstall"), 80),
            installer_manifest=installer_manifest,
            version_slots=version_slots,
            startup_self_checks=startup_self_checks,
            crash_report_records=crash_report_records,
            repair_action_records=repair_action_records,
            installer_last_message=safe_text(data.get("installer_last_message", "安装器 RC 前置结构等待自检"), 220),
            startup_self_check_state=safe_text(data.get("startup_self_check_state", installer_manifest.startup_self_check_state or "pending"), 80),
            update_channel=safe_text(data.get("update_channel", installer_manifest.update_channel or "internal_rc"), 80),
            action_guard_contract=safe_text(data.get("action_guard_contract", ACTION_GUARD_CONTRACT_VERSION), 100),
            action_guard_cards=action_guard_cards,
            audit_readonly_cards=audit_readonly_cards,
            rollback_readonly_cards=rollback_readonly_cards,
            last_confirmation_request=dict(data.get("last_confirmation_request", {}) or {}),
            confirmation_request_state=safe_text(data.get("confirmation_request_state", "idle"), 80),
            provider_settings_contract=safe_text(data.get("provider_settings_contract", PROVIDER_SETTINGS_WRITE_CONTRACT_VERSION), 100),
            provider_config_state=safe_text(data.get("provider_config_state", "idle"), 80),
            provider_config_message=safe_text(data.get("provider_config_message", "未提交 Runtime Provider 设置"), 220),
            provider_config_error_code=safe_text(data.get("provider_config_error_code", ""), 80),
            provider_config_audit_id=safe_text(data.get("provider_config_audit_id", ""), 80),
            provider_api_key_configured=bool(data.get("provider_api_key_configured", False)),
            provider_api_key_digest=safe_text(data.get("provider_api_key_digest", ""), 32),
            provider_base_url_configured=bool(data.get("provider_base_url_configured", False)),
            provider_base_url_digest=safe_text(data.get("provider_base_url_digest", ""), 32),
            last_provider_check_state=safe_text(data.get("last_provider_check_state", "not_tested"), 60),
            last_provider_error_code=safe_text(data.get("last_provider_error_code", ""), 80),
            last_provider_error_message=safe_text(data.get("last_provider_error_message", ""), 180),
            last_provider_next_action=safe_text(data.get("last_provider_next_action", "发送一条短消息完成真实链路联调"), 120),
            stream_state=safe_text(data.get("stream_state", "idle"), 40),
            reconnect_attempts=int(data.get("reconnect_attempts", 0) or 0),
            last_event_seq=int(data.get("last_event_seq", 0) or 0),
            terminal_order_valid=bool(data.get("terminal_order_valid", True)),
            control_state=safe_text(data.get("control_state", "ready"), 80),
            active_run_id=safe_text(data.get("active_run_id", data.get("session_id", "")), 80),
            active_task_id=safe_text(data.get("active_task_id", ""), 80),
            run_workbench_contract=safe_text(data.get("run_workbench_contract", RUN_WORKBENCH_CONTRACT_VERSION), 100),
            run_workbench=run_workbench,
            run_workbench_state=normalize_run_state(data.get("run_workbench_state", run_workbench.state)),
            run_status_label=safe_text(data.get("run_status_label", run_workbench.label or run_state_label(run_workbench.state)), 40),
            frontend_work_mode=safe_text(data.get("frontend_work_mode", run_workbench.frontend_work_mode), 40),
            current_tool_name=safe_text(data.get("current_tool_name", run_workbench.current_tool_name), 80),
            current_tool_status=safe_text(data.get("current_tool_status", run_workbench.current_tool_status), 80),
            waiting_approval_ticket_id=safe_text(data.get("waiting_approval_ticket_id", run_workbench.waiting_ticket_id), 80),
            run_heartbeat_count=int(data.get("run_heartbeat_count", run_workbench.heartbeat_count) or 0),
            run_heartbeat_age_ms=int(data.get("run_heartbeat_age_ms", run_workbench.heartbeat_age_ms) or 0),
            run_last_event=safe_text(data.get("run_last_event", run_workbench.last_event), 80),
            run_last_event_at=safe_text(data.get("run_last_event_at", run_workbench.last_event_at), 80),
            run_reconnect_available=bool(data.get("run_reconnect_available", run_workbench.reconnect_available)),
            run_resume_available=bool(data.get("run_resume_available", run_workbench.resume_available)),
            run_stop_available=bool(data.get("run_stop_available", run_workbench.stop_available)),
            run_diagnostic_summary=safe_text(data.get("run_diagnostic_summary", run_workbench.diagnostic_summary), 260),
            frontend_executes_tools=False,
            current_task_status=safe_text(data.get("current_task_status", "RUNNING"), 40),
            progress_percent=max(0, min(100, int(data.get("progress_percent", 67) or 0))),
            plan_id=safe_text(data.get("plan_id", "plan_20250515_p0_integration"), 120),
            current_stage=safe_text(data.get("current_stage", "接口联调与验证"), 80),
            eta=safe_text(data.get("eta", "2025-05-15 13:30"), 80),
            success_count=int(data.get("success_count", 8) or 0),
            blocked_count=int(data.get("blocked_count", 2) or 0),
            pending_confirmation_count=int(data.get("pending_confirmation_count", 0) or 0),
            execution_stage=safe_text(data.get("execution_stage", "接口联调中"), 80),
            execution_steps=steps,
            quality_decision=safe_text(data.get("quality_decision", "CONDITIONAL"), 64),
            quality_allow_continue=bool(data.get("quality_allow_continue", True)),
            quality_allow_package=bool(data.get("quality_allow_package", False)),
            quality_gate_status=safe_text(data.get("quality_gate_status", "warning"), 64),
            blocking_reasons=blocking,
            audit_count=int(data.get("audit_count", 128) or 0),
            evidence_ref=safe_text(data.get("evidence_ref", "EV-250515-0001"), 80),
            memory_sanitized_summary=safe_text(data.get("memory_sanitized_summary", ""), 260),
            memory_digest=safe_text(data.get("memory_digest", ""), 80),
            memory_evidence_ref=safe_text(data.get("memory_evidence_ref", ""), 80),
            recovery_ticket_id=safe_text(data.get("recovery_ticket_id", ""), 100),
            recovery_failure_count=int(data.get("recovery_failure_count", 0) or 0),
            recovery_resume_plan_count=int(data.get("recovery_resume_plan_count", 0) or 0),
            recovery_next_actions=recovery_actions,
            recovery_requires_human_confirmation=bool(data.get("recovery_requires_human_confirmation", False)),
            chat_messages=messages,
            pending_confirmations=list(data.get("pending_confirmations", []) or []),
            delivery_artifacts=list(data.get("delivery_artifacts", []) or []),
            source_kind=safe_text(data.get("source_kind", "mock"), 64),
            task_snapshot=TaskSnapshotProjection.from_mapping(data.get("task_snapshot", {}) or {}),
            conversation_guide=ConversationGuideRoute.from_mapping(data.get("conversation_guide", {}) or {}),
            four_path_status=FourPathStatusProjection.from_mapping(data.get("four_path_status", {}) or {}),
            self_iteration_projection=SelfIterationFrontendProjection.from_mapping(data.get("self_iteration_projection", {}) or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def append_user_message(self, text: str, timestamp: str = "") -> None:
        timestamp = timestamp or time.strftime("%H:%M:%S")
        self.chat_messages.append(ChatMessage("user", "你", timestamp, safe_chat_text(text, CHAT_USER_INPUT_LIMIT)))
        self.chat_messages.append(
            ChatMessage(
                "assistant",
                "临渊者",
                timestamp,
                "已收到。当前是本地演示回复；需要真实执行时请切换到工作模式。",
            )
        )

    def recent_chat_contains(self, *keywords: str, window: int = 20) -> bool:
        """Return True if a recent chat message contains all supplied keywords.

        This is a UI transcript de-duplication guard. It does not change Runtime
        state, ticket state, audit state, or tool execution behavior.
        """
        clean_keywords = [safe_text(item, 160) for item in keywords if safe_text(item, 160)]
        if not clean_keywords:
            return False
        for item in self.chat_messages[-max(1, int(window)) :]:
            body = str(getattr(item, "text", ""))
            if all(keyword in body for keyword in clean_keywords):
                return True
        return False

    def append_chat_message_once(self, message: ChatMessage, *keywords: str, window: int = 20) -> bool:
        """Append a chat message unless the recent transcript already has it.

        When keywords are omitted, the whole message text is used as the key.
        The guard only prevents repetitive UI notices caused by repeated clicks,
        F5 refresh, or repeated HTTP fallback; it never suppresses user messages.
        """
        dedupe_keywords = keywords or (safe_text(getattr(message, "text", ""), 500),)
        if self.recent_chat_contains(*dedupe_keywords, window=window):
            return False
        self.chat_messages.append(message)
        return True

    def append_assistant_notice_once(self, channel: str, text: str, *keywords: str, window: int = 20) -> bool:
        """Append one idempotent assistant notice for UI/status side effects.

        This is the L6.71.7 transcript root guard: file handoff, connector
        registration, installer self-check, control fallback and confirmation
        notices must be idempotent across repeated clicks, refresh and reconnect.
        Model/user conversational content still uses explicit message append.
        """
        message = ChatMessage("assistant", "临渊者", safe_text(channel, 40) or "状态", safe_chat_text(text, 3000))
        return self.append_chat_message_once(message, *(keywords or (text,)), window=window)

    def add_file_transfer_record(self, record: FileTransferPublicRecord) -> None:
        self.file_transfer_records.append(record)
        self.file_transfer_records = self.file_transfer_records[-20:]
        self.file_transfer_state = safe_text(record.status, 80)
        self.file_transfer_last_message = safe_text(record.message or record.status, 220)
        notice = f"文件传输请求已记录：{safe_text(record.file_name, 100)} · {safe_text(record.status, 40)}。前端未直接调用工具、写记忆或写审计。"
        self.append_assistant_notice_once("文件", notice, "文件传输请求已记录", safe_text(record.file_name, 100), safe_text(record.status, 40), window=20)

    def add_file_authorization_record(self, record: FileAuthorizationPublicRecord) -> None:
        self.file_authorization_records.append(record)
        self.file_authorization_records = self.file_authorization_records[-40:]
        self.workspace_state = safe_text(record.status, 80)
        self.workspace_last_message = safe_text(record.message or record.status, 220)
        notice = f"文件授权请求已记录：{safe_text(record.file_name, 100)} · {safe_text(record.mode, 30)} · {safe_text(record.status, 40)}。真实授权仍由 Runtime / QualityGate 裁决。"
        self.append_assistant_notice_once("工作区", notice, "文件授权请求已记录", safe_text(record.file_name, 100), safe_text(record.mode, 30), safe_text(record.status, 40), window=20)

    def add_download_handoff_record(self, record: DownloadHandoffRecord) -> None:
        self.download_handoff_records.append(record)
        self.download_handoff_records = self.download_handoff_records[-40:]
        self.workspace_state = safe_text(record.status, 80)
        self.workspace_last_message = safe_text(record.message or record.status, 220)

    def add_connector_registration_record(self, record: ConnectorRegistrationPublicRecord) -> None:
        self.connector_registration_records.append(record)
        self.connector_registration_records = self.connector_registration_records[-40:]
        self.connector_registry_state = safe_text(record.status, 80)
        self.connector_last_message = safe_text(record.message or record.status, 220)
        manifest = ConnectorManifestProjection(
            connector_id_digest=record.manifest_digest or digest_text(record.display_name, 16),
            display_name=record.display_name or "未命名连接器",
            kind=record.kind,
            trust_level=record.trust_level,
            default_mode=record.default_mode or "disabled",
            requested_scopes=record.requested_scopes,
            manifest_digest=record.manifest_digest,
            source_digest=record.source_digest,
            signature_digest=record.signature_digest,
            status=record.status,
            quarantined=record.quarantined,
            read_only_default=True,
            quality_gate_required=True,
            workspace_authorization_required=True,
            runtime_authority_required=True,
        )
        self.connector_manifests.append(manifest)
        self.connector_manifests = self.connector_manifests[-40:]
        object.__setattr__(self.connector_registry_projection, "connector_count", len(self.connector_manifests))
        object.__setattr__(self.connector_registry_projection, "read_only_count", sum(1 for item in self.connector_manifests if item.read_only_default))
        object.__setattr__(self.connector_registry_projection, "quarantined_count", sum(1 for item in self.connector_manifests if item.quarantined))
        notice = f"连接器注册请求已记录：{safe_text(record.display_name, 100)} · {safe_text(record.status, 40)}。真实安装/执行仍由 Runtime / QualityGate / 工作区授权裁决。"
        self.append_assistant_notice_once("连接器", notice, "连接器注册请求已记录", safe_text(record.display_name, 100), safe_text(record.status, 40), window=20)

    def record_session_resume_request(self, session_id_digest: str, status: str = "frontend_only_recorded", message: str = "") -> None:
        safe_session = safe_text(session_id_digest, 80)
        safe_status = safe_text(status, 80)
        safe_message = safe_text(message or "恢复请求已记录；真实恢复仍由 Runtime / TiangongWangguan 裁决。", 220)
        if safe_session.upper().startswith("SESS-MOCK"):
            # STEP31E: discard legacy demo resume requests; they are not real work.
            self.task_sessions = [
                item for item in self.task_sessions
                if not safe_text(getattr(item, "session_id_digest", ""), 80).upper().startswith("SESS-MOCK")
            ]
            self.session_manager_state = "mock_session_discarded"
            self.session_last_message = "已清理旧版演示 Session；未向 Runtime 提交恢复请求。"
            self.session_stats = SessionManagerStats.from_sessions(self.task_sessions).to_dict()
            return
        updated = []
        found = False
        for item in self.task_sessions:
            if safe_text(item.session_id_digest, 80) == safe_session:
                found = True
                updated.append(TaskSessionProjection(
                    session_id_digest=item.session_id_digest,
                    title=item.title,
                    status="recoverable" if safe_status.startswith("frontend") else safe_status,
                    current_stage="恢复请求已提交 Runtime" if safe_status else item.current_stage,
                    progress_percent=item.progress_percent,
                    waiting_confirmation=item.waiting_confirmation,
                    blocked=item.blocked,
                    recoverable=True,
                    active=item.active,
                    last_updated="当前",
                    run_id_digest=item.run_id_digest,
                    task_id_digest=item.task_id_digest,
                    audit_id=item.audit_id,
                    tags=list(item.tags or [])[:8],
                    message=safe_message,
                ))
            else:
                updated.append(item)
        if not found:
            updated.append(TaskSessionProjection(
                session_id_digest=safe_session or digest_text("unknown-session", 16),
                title="手动恢复请求",
                status="recoverable",
                current_stage="恢复请求已提交 Runtime",
                progress_percent=0,
                recoverable=True,
                last_updated="当前",
                tags=["manual_resume"],
                message=safe_message,
            ))
        self.task_sessions = updated[-80:]
        self.session_manager_state = safe_status or "resume_requested"
        self.session_last_message = safe_message
        self.session_stats = SessionManagerStats.from_sessions(self.task_sessions).to_dict()
        # Do not append resume notices into the chat transcript. The task tower
        # already shows the request state; chat spam here looked like QualityGate
        # output and confused active conversations.

    def record_session_search(self, query: str) -> None:
        safe_query = safe_text(query, 120)
        self.session_search_query = safe_query
        if not safe_query:
            self.session_filtered_count = len(self.task_sessions)
        else:
            q = safe_query.lower()
            self.session_filtered_count = sum(
                1 for item in self.task_sessions
                if q in item.title.lower() or q in item.status.lower() or q in item.current_stage.lower() or any(q in tag.lower() for tag in item.tags)
            )
        self.session_last_message = f"搜索条件已记录：{safe_query or '全部'}；过滤命中 {self.session_filtered_count} 个任务。"

    def record_installer_self_check_result(self, checks: List[StartupSelfCheckRecord], status: str = "frontend_only_recorded") -> None:
        self.startup_self_checks = list(checks)[-40:]
        summary = summarize_checks(self.startup_self_checks)
        blocked = int(summary.get("blocked", 0) or 0) + int(summary.get("fail", 0) or 0)
        self.startup_self_check_state = "blocked" if blocked else safe_text(status, 80)
        self.installer_last_message = f"启动自检记录已更新：pass={summary.get('pass', 0)} warn={summary.get('warn', 0)} blocked={blocked}。前端未应用更新或回滚。"
        if not self.installer_manifest.startup_checks:
            object.__setattr__(self.installer_manifest, "startup_checks", self.startup_self_checks[:])
        self.append_assistant_notice_once("安装", self.installer_last_message, "启动自检记录已更新", str(summary.get("pass", 0)), str(summary.get("warn", 0)), str(blocked), window=20)

    def submit_confirmation(self, ticket_id: str, decision: str) -> None:
        safe_ticket = safe_text(ticket_id, 80)
        safe_decision = safe_text(decision, 32)
        self.confirmation_request_state = "frontend_only_recorded"
        self.last_confirmation_request = {
            "ticket_id": safe_ticket,
            "decision": safe_decision,
            "frontend_only": True,
            "route_to_runtime_only": False,
            "no_frontend_execute": True,
            "no_frontend_gate_bypass": True,
            "no_frontend_audit_write": True,
            "no_frontend_rollback_apply": True,
        }
        for item in self.pending_confirmations:
            if safe_text(item.get("ticket_id", ""), 80) == safe_ticket:
                item["frontend_decision"] = safe_decision
                item["frontend_only"] = True
        for card in self.action_guard_cards:
            if safe_text(getattr(card, "ticket_id", ""), 80) == safe_ticket:
                object.__setattr__(card, "status", f"frontend_{safe_decision}_recorded")
        self.append_chat_message_once(
            ChatMessage(
                "assistant",
                "临渊者",
                "当前",
                f"确认票据 {safe_ticket} 已在前端层记录为 {safe_decision} 请求；未触发工具、审计写入或回滚。",
            ),
            "确认票据",
            safe_ticket,
            safe_decision,
            window=20,
        )

    def submit_self_iteration_confirmation(self, candidate_id: str, decision: str, *, runtime_submitted: bool = False, runtime_status: str = "") -> None:
        safe_candidate = safe_text(candidate_id, 80)
        safe_decision = safe_text(decision, 32)
        safe_status = safe_text(runtime_status, 80)
        for item in self.self_iteration_projection.candidates:
            if safe_text(item.candidate_id, 80) == safe_candidate:
                item.status = f"runtime_{safe_status or safe_decision}" if runtime_submitted else f"frontend_{safe_decision}"
        self.self_iteration_projection.pending_count = sum(
            1 for item in self.self_iteration_projection.candidates if item.status == "pending_user_confirmation"
        )
        message = (
            f"自我迭代候选 {safe_candidate} 已提交 Runtime 网关：{safe_status or safe_decision}；不由前端直接合入。"
            if runtime_submitted
            else f"自我迭代候选 {safe_candidate} 已在前端层记录为 {safe_decision}；真实更新仍需 Planner / ExecutionSpine / QualityGate。"
        )
        self.append_chat_message_once(
            ChatMessage("assistant", "临渊者", "自我迭代", message),
            "自我迭代候选",
            safe_candidate,
            safe_decision,
            window=20,
        )
