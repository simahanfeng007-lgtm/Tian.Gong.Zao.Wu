"""L6.37 执行链全线贯通冻结契约。

本模块把 L6.33-L6.36 已压实的执行链收束成后续系统接入的唯一边界说明：
Planner/CLI/系统插件只能提交 Step、Ticket、Evidence、Hint；真实执行必须经
``PlannerExecutionController -> LongChainRunner -> ExecutionSpine -> PermitGateway -> Registry -> Adapter -> AuditBridge``。

它不执行工具、不读取密钥、不注册插件、不修改 ``tiangong_kernel``。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .planner_execution_controller import PLANNER_EXECUTION_SCHEMA, stable_planner_execution_digest
from .recovery_replay_quality import L6_36_SCHEMA

L6_37_SCHEMA = "tiangong.l6_37.execution_chain_freeze.v1"
L6_37_SOURCE_VERSION = "L6.37-execution-chain-freeze-baseline"

REQUIRED_REPORT_FLAGS = (
    "execution_first",
    "runtime_governed",
    "uses_long_chain_runner",
    "uses_execution_spine",
    "replayable",
    "resumable",
    "no_parallel_runtime",
    "no_direct_adapter_call",
    "no_registry_mutation",
    "no_kernel_mutation",
    "no_secret_read",
    "no_provider_call",
)

FORBIDDEN_EXECUTION_CHANNELS = (
    "plugin_direct_tool_call",
    "provider_naked_sdk_call",
    "skill_direct_activation",
    "handoff_recursive_spawn_without_ticket",
    "frontend_bypass_planner_execution_controller",
    "direct_adapter_call_outside_execution_spine",
    "registry_mutation_during_task_run",
    "kernel_mutation_from_l6_shell",
    "secret_read_in_planner_or_report",
)

ALLOWED_RUNTIME_FACADE_METHODS = (
    "RuntimeEntry.run_planner_execution_task",
    "RuntimeEntry.execute_plan",
    "RuntimeEntry.resume_plan",
    "RuntimeEntry.confirm_ticket",
)

GOVERNED_CHAIN = (
    "CLI/API/UserTask",
    "SessionContextInjection",
    "ModelPlanner/RulePlanner/HybridPlanner",
    "DeepSeekPlanShapeNormalizer",
    "PlanSchemaValidator",
    "PlannerExecutionController",
    "LongChainRunner",
    "ExecutionSpine",
    "RiskClassifier",
    "PermitGateway",
    "RuntimeToolRegistry",
    "Adapter",
    "AuditBridge",
    "PlannerExecutionReport",
    "L6.36FailureRecoveryReplayQuality",
)


@dataclass(frozen=True)
class ExecutionChainContract:
    """后续系统接入执行链的冻结契约。"""

    schema: str = L6_37_SCHEMA
    source_version: str = L6_37_SOURCE_VERSION
    status: str = "frozen"
    chain_name: str = "临渊者 L6 执行链全线贯通唯一入口"
    governed_chain: tuple[str, ...] = GOVERNED_CHAIN
    allowed_runtime_facade_methods: tuple[str, ...] = ALLOWED_RUNTIME_FACADE_METHODS
    required_report_flags: tuple[str, ...] = REQUIRED_REPORT_FLAGS
    forbidden_execution_channels: tuple[str, ...] = FORBIDDEN_EXECUTION_CHANNELS
    planner_step_contract: dict[str, Any] = field(default_factory=dict)
    adapter_contract: dict[str, Any] = field(default_factory=dict)
    ticket_contract: dict[str, Any] = field(default_factory=dict)
    evidence_contract: dict[str, Any] = field(default_factory=dict)
    report_contract: dict[str, Any] = field(default_factory=dict)
    system_mount_contract: dict[str, Any] = field(default_factory=dict)
    no_second_runtime: bool = True
    no_direct_tool_release: bool = True
    no_kernel_mutation: bool = True
    no_secret_read: bool = True
    future_systems_must_use_contract: bool = True

    def __post_init__(self) -> None:
        if self.schema != L6_37_SCHEMA:
            raise ValueError("L6.37 contract schema mismatch")
        if self.status != "frozen":
            raise ValueError("L6.37 contract must be frozen")
        if not all((self.no_second_runtime, self.no_direct_tool_release, self.no_kernel_mutation, self.no_secret_read, self.future_systems_must_use_contract)):
            raise ValueError("L6.37 contract boundary flags must stay true")
        if "PlannerExecutionController" not in self.governed_chain:
            raise ValueError("L6.37 governed chain must include PlannerExecutionController")
        if "ExecutionSpine" not in self.governed_chain:
            raise ValueError("L6.37 governed chain must include ExecutionSpine")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "source_version": self.source_version,
            "status": self.status,
            "chain_name": self.chain_name,
            "governed_chain": list(self.governed_chain),
            "allowed_runtime_facade_methods": list(self.allowed_runtime_facade_methods),
            "required_report_flags": list(self.required_report_flags),
            "forbidden_execution_channels": list(self.forbidden_execution_channels),
            "planner_step_contract": self.planner_step_contract or default_planner_step_contract(),
            "adapter_contract": self.adapter_contract or default_adapter_contract(),
            "ticket_contract": self.ticket_contract or default_ticket_contract(),
            "evidence_contract": self.evidence_contract or default_evidence_contract(),
            "report_contract": self.report_contract or default_report_contract(),
            "system_mount_contract": self.system_mount_contract or default_system_mount_contract(),
            "no_second_runtime": self.no_second_runtime,
            "no_direct_tool_release": self.no_direct_tool_release,
            "no_kernel_mutation": self.no_kernel_mutation,
            "no_secret_read": self.no_secret_read,
            "future_systems_must_use_contract": self.future_systems_must_use_contract,
        }

    def export_json(self, path: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def markdown_report(self) -> str:
        payload = self.public_dict()
        lines = [
            "# 临渊者 L6.37 执行链冻结契约",
            "",
            f"- schema: `{payload['schema']}`",
            f"- source_version: `{payload['source_version']}`",
            f"- status: `{payload['status']}`",
            "",
            "## 唯一治理链",
            "",
        ]
        for item in payload["governed_chain"]:
            lines.append(f"- {item}")
        lines.extend(["", "## 禁止第二执行通道", ""])
        for item in payload["forbidden_execution_channels"]:
            lines.append(f"- {item}")
        lines.extend([
            "",
            "## 后续系统接入原则",
            "",
            "Provider、Skill、Handoff、预算、回滚、情志、前端、安装产品化等系统只能提交 Hint / Step / Ticket / Evidence / Report，不能直接执行工具、裸调模型 SDK、激活 Skill、派生子智能体或修改内核。",
        ])
        return "\n".join(lines)


@dataclass(frozen=True)
class ExecutionChainFreezeReport:
    """基于最近 PlannerExecutionReport 生成的冻结验收报告。"""

    schema: str
    source_version: str
    status: str
    ready: bool
    source_execution_schema: str
    source_execution_status: str
    source_report_digest: str
    l6_36_ready: bool
    contract: ExecutionChainContract
    issues: list[str] = field(default_factory=list)
    checked_report_flags: dict[str, bool] = field(default_factory=dict)
    execution_chain_ready: bool = True
    can_accept_future_system_mounts: bool = True
    no_second_runtime: bool = True
    no_direct_adapter_call: bool = True
    no_kernel_mutation: bool = True
    no_secret_read: bool = True

    def __post_init__(self) -> None:
        if self.schema != L6_37_SCHEMA:
            raise ValueError("L6.37 freeze report schema mismatch")
        if not all((self.no_second_runtime, self.no_direct_adapter_call, self.no_kernel_mutation, self.no_secret_read)):
            raise ValueError("L6.37 freeze report boundary flags must stay true")
        if self.ready and self.issues:
            raise ValueError("L6.37 freeze report cannot be ready with unresolved issues")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "source_version": self.source_version,
            "status": self.status,
            "ready": self.ready,
            "source_execution_schema": self.source_execution_schema,
            "source_execution_status": self.source_execution_status,
            "source_report_digest": self.source_report_digest,
            "l6_36_ready": self.l6_36_ready,
            "issues": list(self.issues),
            "checked_report_flags": dict(self.checked_report_flags),
            "execution_chain_ready": self.execution_chain_ready,
            "can_accept_future_system_mounts": self.can_accept_future_system_mounts,
            "no_second_runtime": self.no_second_runtime,
            "no_direct_adapter_call": self.no_direct_adapter_call,
            "no_kernel_mutation": self.no_kernel_mutation,
            "no_secret_read": self.no_secret_read,
            "contract": self.contract.public_dict(),
        }

    def export_json(self, path: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def markdown_report(self) -> str:
        payload = self.public_dict()
        lines = [
            "# 临渊者 L6.37 执行链冻结验收报告",
            "",
            f"- status: `{payload['status']}`",
            f"- ready: `{payload['ready']}`",
            f"- source_execution_status: `{payload['source_execution_status']}`",
            f"- source_report_digest: `{payload['source_report_digest']}`",
            f"- l6_36_ready: `{payload['l6_36_ready']}`",
            "",
            "## 报告旗标检查",
            "",
        ]
        for key, ok in payload["checked_report_flags"].items():
            lines.append(f"- {key}: `{ok}`")
        if payload["issues"]:
            lines.extend(["", "## 未解决问题", ""])
            for issue in payload["issues"]:
                lines.append(f"- {issue}")
        else:
            lines.extend(["", "## 结论", "", "执行链已满足 L6.37 冻结条件；后续系统必须接入该统一治理链。"])
        return "\n".join(lines)


def build_default_execution_chain_contract() -> ExecutionChainContract:
    return ExecutionChainContract()


def build_execution_chain_freeze_report(planner_execution_payload: dict[str, Any] | None) -> ExecutionChainFreezeReport:
    contract = build_default_execution_chain_contract()
    payload = dict(planner_execution_payload or {})
    issues: list[str] = []
    source_schema = str(payload.get("schema") or "")
    source_status = str(payload.get("status") or "empty")
    if not payload or source_status == "empty":
        issues.append("missing_planner_execution_report")
    if source_schema != PLANNER_EXECUTION_SCHEMA:
        issues.append("planner_execution_schema_not_current")

    checked_flags: dict[str, bool] = {}
    for flag in REQUIRED_REPORT_FLAGS:
        checked_flags[flag] = bool(payload.get(flag) is True)
        if not checked_flags[flag]:
            issues.append(f"report_flag_not_true:{flag}")

    l6_36 = dict(payload.get("l6_36") or {})
    l6_36_ready = bool(l6_36.get("schema") == L6_36_SCHEMA and l6_36.get("execution_chain_ready") is True)
    if not l6_36_ready:
        issues.append("l6_36_quality_recovery_replay_not_ready")

    report_digest = str(payload.get("report_digest") or "")
    if not report_digest and payload:
        report_digest = stable_planner_execution_digest(payload)
    if not report_digest:
        issues.append("missing_source_report_digest")

    ready = not issues
    status = "frozen" if ready else "not_ready"
    return ExecutionChainFreezeReport(
        schema=L6_37_SCHEMA,
        source_version=L6_37_SOURCE_VERSION,
        status=status,
        ready=ready,
        source_execution_schema=source_schema,
        source_execution_status=source_status,
        source_report_digest=report_digest,
        l6_36_ready=l6_36_ready,
        contract=contract,
        issues=issues,
        checked_report_flags=checked_flags,
    )


def default_planner_step_contract() -> dict[str, Any]:
    return {
        "accepted_input": "ToolInvocation generated from PlanSchema / ModelPlanner / explicit Runtime API",
        "required_fields": ["tool_name", "arguments", "step_id"],
        "optional_fields": ["parent_step_id", "source_plan_id", "risk_level", "expected_output"],
        "lifecycle_states": ["planned", "queued", "running", "succeeded", "failed", "blocked", "confirmation_required", "skipped", "recovered", "timeout"],
        "rules": [
            "Planner only proposes steps; it cannot execute them.",
            "All non-standard model output must be normalized before validation.",
            "Unsafe or unknown plans must fail closed with diagnostic reasons.",
        ],
    }


def default_adapter_contract() -> dict[str, Any]:
    return {
        "entry": "ExecutionSpine.execute",
        "registry": "RuntimeToolRegistry",
        "permission": "PermitGateway + RiskClassifier",
        "audit": "AuditBridge",
        "rules": [
            "Adapters are never called directly by plugins, Provider adapters, Skill candidates, GUI, or handoff agents.",
            "Registry mutation is not allowed during task execution.",
            "Provider network calls require explicit ProviderExecutionTicket in later phases; L6.37 freeze itself performs no provider call.",
        ],
    }


def default_ticket_contract() -> dict[str, Any]:
    return {
        "confirmation": "A4 produces ConfirmationTicket and pauses execution.",
        "blocked": "A5 produces hard stop and replan requirement.",
        "resume": "ResumeEnvelope is advisory; it cannot execute by itself.",
        "rules": [
            "Tickets cannot be issued by affective/free-will projection as authorization.",
            "Skill activation, tool registration, provider credential use, and hot switch require explicit governance ticket in later phases.",
        ],
    }


def default_evidence_contract() -> dict[str, Any]:
    return {
        "evidence_types": ["audit_ref", "checkpoint_ref", "replay_event", "quality_gate_result", "resume_envelope", "delivery_integrity"],
        "redaction": "Secrets, raw credentials, full private content, and kernel paths must be redacted from public reports.",
        "rules": [
            "Every executed step should produce audit or checkpoint evidence.",
            "Skipped steps must be replayable from report state.",
            "Timeout and blocked states must remain distinguishable from ordinary failure.",
        ],
    }


def default_report_contract() -> dict[str, Any]:
    return {
        "primary_report": "PlannerExecutionReport.public_dict",
        "l6_36_enrichment": "FailureClassification + RecoveryPlan + ReplayReport + QualityGateResult",
        "stable_digest": "stable_planner_execution_digest",
        "required_public_sections": ["step_records", "replay_events", "resume_envelope", "progress_snapshots", "l6_36"],
        "rules": [
            "Reports are evidence artifacts, not execution permissions.",
            "A report must preserve enough data to replay order and resume decisions without exposing secrets.",
        ],
    }


def default_system_mount_contract() -> dict[str, Any]:
    return {
        "future_system_output_types": ["Hint", "StepDraft", "TicketRequest", "Evidence", "Report", "ResumeEnvelope"],
        "must_enter": "PlannerExecutionController / RuntimeEntry façade",
        "must_not_create": ["second_runtime", "direct_tool_channel", "direct_provider_channel", "direct_skill_activation_channel"],
        "next_system_batches": [
            "Provider/Budget/Skill/Handoff",
            "Rollback/SelfRepair/SelfLearning",
            "AffectiveFreeWill/AuditProjection/PluginSuggestion",
            "GUI/WindowsInstall/ThreeEndpointProductization",
        ],
    }
