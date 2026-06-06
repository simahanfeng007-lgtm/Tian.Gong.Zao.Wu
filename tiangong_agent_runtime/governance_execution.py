"""L6.30 治理执行力化外壳。

本模块把权限、审计、预算、质量门和恢复链压缩成 Planner 可直接消费的
治理执行提示。它不修改 PermitGateway / ExecutionPolicy 的真实策略，不确认票据，
不调用工具，不写文件，不改预算，不注册 Tool/Skill，不触碰 tiangong_kernel。

执行力口径：A0-A4 的草案、分析、smoke、续接默认走快车道；发布、注册、激活、
真实外部副作用仍由质量门/确认/审计护栏拦住；A5 保持硬边界。
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import Any

from tiangong_agent_shell.safe_logging import redact_text

from .tool_invocation import ToolInvocation
from .tool_result import ToolResult, ToolResultStatus
from .turn_context import TurnContext

GOVERNANCE_EXECUTION_SCHEMA = "tiangong.l6_30.governance_execution.v1"
A0_A4_LEVELS = ("A0", "A1", "A2", "A3", "A4")
SENSITIVE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer|token|secret|password|credential)\s*[:=]\s*[^\s,;]+"
)
SENSITIVE_WORDS = ("api_key", "apikey", "authorization", "bearer", "token", "secret", "password", "credential")


@dataclass(frozen=True)
class GovernanceFastLane:
    """A0-A4 执行快车道。只描述策略，不改真实 PermitGateway。"""

    lane_ref: str
    lane_name: str
    risk_levels: tuple[str, ...]
    action_kinds: tuple[str, ...]
    planner_policy: str
    quality_gate_position: str
    requires_confirmation: bool = False
    runtime_governed: bool = True
    direct_execution_now: bool = False
    mutates_policy: bool = False

    def __post_init__(self) -> None:
        if any(level not in A0_A4_LEVELS for level in self.risk_levels):
            raise ValueError("L6.30 fast lane can only cover A0-A4")
        if self.requires_confirmation or not self.runtime_governed or self.direct_execution_now or self.mutates_policy:
            raise ValueError("L6.30 fast lane must remain runtime-governed, no-confirmation draft lane")

    def public_dict(self) -> dict[str, Any]:
        return {
            "lane_ref": self.lane_ref,
            "lane_name": self.lane_name,
            "risk_levels": list(self.risk_levels),
            "action_kinds": list(self.action_kinds),
            "planner_policy": self.planner_policy,
            "quality_gate_position": self.quality_gate_position,
            "requires_confirmation": self.requires_confirmation,
            "runtime_governed": self.runtime_governed,
            "direct_execution_now": self.direct_execution_now,
            "mutates_policy": self.mutates_policy,
        }


@dataclass(frozen=True)
class GovernanceBoundary:
    """治理边界。A5 硬拦；发布/注册/激活走发布护栏。"""

    boundary_ref: str
    boundary_name: str
    trigger: str
    risk_level: str
    action: str
    blocks_execution: bool
    requires_confirmation: bool = False
    quality_gate_required: bool = False
    release_or_activation_gate: bool = False
    hard_boundary: bool = False

    def __post_init__(self) -> None:
        if self.risk_level == "A5" and not (self.blocks_execution and self.hard_boundary):
            raise ValueError("L6.30 A5 boundary must block execution as hard boundary")
        if self.hard_boundary and not self.blocks_execution:
            raise ValueError("L6.30 hard boundary cannot be non-blocking")

    def public_dict(self) -> dict[str, Any]:
        return {
            "boundary_ref": self.boundary_ref,
            "boundary_name": self.boundary_name,
            "trigger": self.trigger,
            "risk_level": self.risk_level,
            "action": self.action,
            "blocks_execution": self.blocks_execution,
            "requires_confirmation": self.requires_confirmation,
            "quality_gate_required": self.quality_gate_required,
            "release_or_activation_gate": self.release_or_activation_gate,
            "hard_boundary": self.hard_boundary,
        }


@dataclass(frozen=True)
class GovernanceDecisionDraft:
    """Planner 可消费的治理判定草案，不是真实 PermitDecision。"""

    decision_ref: str
    source_ref: str
    tool_or_action: str
    risk_level: str
    action_kind: str
    lane_ref: str
    status: str
    reason: str
    planner_next: str
    direct_execution_now: bool = False
    bypasses_runtime: bool = False
    mutates_policy: bool = False

    def __post_init__(self) -> None:
        if self.direct_execution_now or self.bypasses_runtime or self.mutates_policy:
            raise ValueError("L6.30 decision draft cannot execute, bypass runtime or mutate policy")
        if self.risk_level == "A5" and self.status not in {"blocked", "confirmation_required"}:
            raise ValueError("L6.30 A5 decision draft must block or require confirmation")

    def public_dict(self) -> dict[str, Any]:
        return {
            "decision_ref": self.decision_ref,
            "source_ref": self.source_ref,
            "tool_or_action": self.tool_or_action,
            "risk_level": self.risk_level,
            "action_kind": self.action_kind,
            "lane_ref": self.lane_ref,
            "status": self.status,
            "reason": self.reason,
            "planner_next": self.planner_next,
            "direct_execution_now": self.direct_execution_now,
            "bypasses_runtime": self.bypasses_runtime,
            "mutates_policy": self.mutates_policy,
        }


@dataclass(frozen=True)
class PlannerGovernanceHint:
    """给统一 Planner 的治理提示。"""

    hint_ref: str
    source_ref: str
    title: str
    next_action: str
    lane_ref: str
    stop_condition: str
    planner_consumable: bool = True
    blocks_planner: bool = False
    bypasses_runtime: bool = False

    def __post_init__(self) -> None:
        if not self.planner_consumable or self.blocks_planner or self.bypasses_runtime:
            raise ValueError("L6.30 planner hint must be consumable and cannot block or bypass runtime")

    def public_dict(self) -> dict[str, Any]:
        return {
            "hint_ref": self.hint_ref,
            "source_ref": self.source_ref,
            "title": self.title,
            "next_action": self.next_action,
            "lane_ref": self.lane_ref,
            "stop_condition": self.stop_condition,
            "planner_consumable": self.planner_consumable,
            "blocks_planner": self.blocks_planner,
            "bypasses_runtime": self.bypasses_runtime,
        }


@dataclass(frozen=True)
class GovernanceExecutionReport:
    schema: str
    generated_at: float
    status: str
    summary: str
    fast_lanes: list[GovernanceFastLane] = field(default_factory=list)
    boundaries: list[GovernanceBoundary] = field(default_factory=list)
    decisions: list[GovernanceDecisionDraft] = field(default_factory=list)
    planner_hints: list[PlannerGovernanceHint] = field(default_factory=list)
    source_schemas: list[str] = field(default_factory=list)
    pending_confirmation_count: int = 0
    notes_used: bool = False
    execution_first: bool = True
    shell_only: bool = True
    a0_a4_fast_lane: bool = True
    a5_hard_boundary: bool = True
    release_activation_gated: bool = True
    quality_gate_only_blocks_release: bool = True
    budget_projection_only: bool = True
    audit_projection_only: bool = True
    no_policy_mutation: bool = True
    no_direct_execution: bool = True
    no_registry_mutation: bool = True
    no_kernel_mutation: bool = True
    no_secret_read: bool = True
    no_provider_call: bool = True
    modifies_policy: bool = False
    invokes_tool: bool = False
    writes_file: bool = False
    applies_patch: bool = False
    mutates_budget: bool = False
    registers_tool: bool = False
    registers_skill: bool = False
    touches_kernel: bool = False
    report_digest: str = ""

    def __post_init__(self) -> None:
        required = (
            self.execution_first,
            self.shell_only,
            self.a0_a4_fast_lane,
            self.a5_hard_boundary,
            self.release_activation_gated,
            self.quality_gate_only_blocks_release,
            self.budget_projection_only,
            self.audit_projection_only,
            self.no_policy_mutation,
            self.no_direct_execution,
            self.no_registry_mutation,
            self.no_kernel_mutation,
            self.no_secret_read,
            self.no_provider_call,
        )
        if not all(required):
            raise ValueError("L6.30 governance execution must remain execution-first, shell-only and non-mutating")
        forbidden = (
            self.modifies_policy,
            self.invokes_tool,
            self.writes_file,
            self.applies_patch,
            self.mutates_budget,
            self.registers_tool,
            self.registers_skill,
            self.touches_kernel,
        )
        if any(forbidden):
            raise ValueError("L6.30 governance execution cannot mutate policy/execute/write/register/touch kernel")

    @property
    def fast_lane_count(self) -> int:
        return len(self.fast_lanes)

    @property
    def boundary_count(self) -> int:
        return len(self.boundaries)

    @property
    def hard_boundary_count(self) -> int:
        return sum(1 for item in self.boundaries if item.hard_boundary)

    @property
    def release_gate_count(self) -> int:
        return sum(1 for item in self.boundaries if item.release_or_activation_gate)

    @property
    def decision_count(self) -> int:
        return len(self.decisions)

    @property
    def planner_hint_count(self) -> int:
        return len(self.planner_hints)

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "status": self.status,
            "summary": self.summary,
            "fast_lanes": [item.public_dict() for item in self.fast_lanes],
            "boundaries": [item.public_dict() for item in self.boundaries],
            "decisions": [item.public_dict() for item in self.decisions],
            "planner_hints": [item.public_dict() for item in self.planner_hints],
            "source_schemas": list(self.source_schemas),
            "pending_confirmation_count": self.pending_confirmation_count,
            "notes_used": self.notes_used,
            "execution_first": self.execution_first,
            "shell_only": self.shell_only,
            "a0_a4_fast_lane": self.a0_a4_fast_lane,
            "a5_hard_boundary": self.a5_hard_boundary,
            "release_activation_gated": self.release_activation_gated,
            "quality_gate_only_blocks_release": self.quality_gate_only_blocks_release,
            "budget_projection_only": self.budget_projection_only,
            "audit_projection_only": self.audit_projection_only,
            "no_policy_mutation": self.no_policy_mutation,
            "no_direct_execution": self.no_direct_execution,
            "no_registry_mutation": self.no_registry_mutation,
            "no_kernel_mutation": self.no_kernel_mutation,
            "no_secret_read": self.no_secret_read,
            "no_provider_call": self.no_provider_call,
            "fast_lane_count": self.fast_lane_count,
            "boundary_count": self.boundary_count,
            "hard_boundary_count": self.hard_boundary_count,
            "release_gate_count": self.release_gate_count,
            "decision_count": self.decision_count,
            "planner_hint_count": self.planner_hint_count,
            "modifies_policy": self.modifies_policy,
            "invokes_tool": self.invokes_tool,
            "writes_file": self.writes_file,
            "applies_patch": self.applies_patch,
            "mutates_budget": self.mutates_budget,
            "registers_tool": self.registers_tool,
            "registers_skill": self.registers_skill,
            "touches_kernel": self.touches_kernel,
            "report_digest": self.report_digest,
        }

    def summary_text(self) -> str:
        return (
            "L6.30 治理执行力化："
            f"status={self.status}；fast_lane={self.fast_lane_count}；boundary={self.boundary_count}；"
            f"hard={self.hard_boundary_count}；release_gate={self.release_gate_count}；"
            f"decision={self.decision_count}；hint={self.planner_hint_count}。{self.summary}"
        )

    def markdown_report(self) -> str:
        lines = [
            "# 临渊者 L6.30 治理执行力化报告",
            "",
            f"- schema: `{self.schema}`",
            f"- status: `{self.status}`",
            f"- execution_first: `{self.execution_first}`",
            f"- a0_a4_fast_lane: `{self.a0_a4_fast_lane}`",
            f"- a5_hard_boundary: `{self.a5_hard_boundary}`",
            f"- report_digest: `{self.report_digest}`",
            "",
            "## 摘要",
            "",
            self.summary,
            "",
            "## 快车道",
            "",
        ]
        for item in self.fast_lanes:
            lines.append(f"- `{item.lane_ref}` {item.lane_name}: {item.planner_policy}")
        lines.extend(["", "## 边界", ""])
        for item in self.boundaries:
            lines.append(f"- `{item.boundary_ref}` [{item.risk_level}] {item.boundary_name}: {item.action}")
        lines.extend(["", "## Planner 提示", ""])
        for item in self.planner_hints:
            lines.append(f"- `{item.hint_ref}` {item.title}: {item.next_action}")
        lines.append("")
        lines.append("> L6.30 只生成治理执行提示，不修改真实策略；真实执行仍走 Runtime registry / permit / audit / quality gate 链路。")
        return "\n".join(lines)


class GovernanceExecutionBridge:
    """Runtime 外壳层治理执行力化桥。"""

    def __init__(self) -> None:
        self._last_report: GovernanceExecutionReport | None = None

    @property
    def last_report(self) -> GovernanceExecutionReport | None:
        return self._last_report

    def reset(self) -> None:
        self._last_report = None

    def build(
        self,
        *,
        recovery_report: dict[str, Any] | None = None,
        learning_convergence_report: dict[str, Any] | None = None,
        provider_adaptation_report: dict[str, Any] | None = None,
        delivery_standardization_report: dict[str, Any] | None = None,
        project_repair_report: dict[str, Any] | None = None,
        shell_mount_report: dict[str, Any] | None = None,
        audit_events: list[dict[str, Any]] | None = None,
        pending_confirmations: list[dict[str, Any]] | None = None,
        notes: str = "",
        max_items: int = 12,
    ) -> GovernanceExecutionReport:
        limit = max(1, min(int(max_items), 40))
        safe_notes = _safe_text(notes, limit=700)
        recovery = recovery_report or {}
        learning = learning_convergence_report or {}
        provider = provider_adaptation_report or {}
        delivery = delivery_standardization_report or {}
        repair = project_repair_report or {}
        shell = shell_mount_report or {}
        audit = audit_events or []
        pending = pending_confirmations or []

        fast_lanes = _default_fast_lanes()
        boundaries = _build_boundaries(pending, audit, delivery, provider, safe_notes)
        decisions = _build_decisions(fast_lanes, boundaries, recovery, learning, repair, delivery, provider, limit=limit)
        hints = _build_planner_hints(decisions, recovery, learning, repair, delivery, provider, shell, limit=limit)
        source_schemas = _source_schemas(recovery, learning, provider, delivery, repair, shell)
        status = "governance_execution_ready" if fast_lanes and boundaries and hints else "governance_execution_partial"
        summary = _summary(fast_lanes, boundaries, decisions, hints, len(pending))
        report = GovernanceExecutionReport(
            schema=GOVERNANCE_EXECUTION_SCHEMA,
            generated_at=time(),
            status=status,
            summary=summary,
            fast_lanes=fast_lanes,
            boundaries=boundaries,
            decisions=decisions,
            planner_hints=hints,
            source_schemas=source_schemas,
            pending_confirmation_count=len(pending),
            notes_used=bool(safe_notes),
        )
        report = GovernanceExecutionReport(**{**report.__dict__, "report_digest": stable_governance_execution_digest(report)})
        self._last_report = report
        return report

    def public_dict(self) -> dict[str, Any]:
        if self._last_report is None:
            return {
                "schema": GOVERNANCE_EXECUTION_SCHEMA,
                "status": "empty",
                "message": "暂无 L6.30 治理执行力化报告，请先执行 /governance-build。",
            }
        return self._last_report.public_dict()

    def export_json(self, path: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def build_planner_hint(self) -> str:
        if self._last_report is None or self._last_report.status == "empty":
            return ""
        report = self._last_report
        lanes = ", ".join(item.lane_name for item in report.fast_lanes[:3]) or "无"
        next_actions = "; ".join(item.next_action for item in report.planner_hints[:3]) or "无"
        return (
            "最近 L6.30 治理执行力化："
            f"status={report.status}; fast_lanes={report.fast_lane_count}; hard_boundary={report.hard_boundary_count}; "
            f"release_gate={report.release_gate_count}; a0_a4_fast_lane=True; a5_hard_boundary=True; "
            f"release_activation_gated=True; lanes={lanes}; next={next_actions}; shell_only=True; no_policy_mutation=True"
        )[:1600]


def build_governance_execution_adapter(
    bridge: GovernanceExecutionBridge,
    recovery_coordination: Any,
    learning_convergence: Any,
    provider_adaptation: Any,
    delivery_standardization: Any,
    project_repair: Any,
    shell_mount: Any,
    audit: Any,
    ticket_store: Any,
):
    def governance_execution_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            report = bridge.build(
                recovery_report=recovery_coordination.public_dict(),
                learning_convergence_report=learning_convergence.public_dict(),
                provider_adaptation_report=provider_adaptation.public_dict(),
                delivery_standardization_report=delivery_standardization.public_dict(),
                project_repair_report=project_repair.public_dict(),
                shell_mount_report=shell_mount.public_dict(),
                audit_events=audit.recent_summary() if hasattr(audit, "recent_summary") else [],
                pending_confirmations=ticket_store.public_pending() if hasattr(ticket_store, "public_pending") else [],
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
                max_items=int(invocation.arguments.get("max_items") or 12),
            )
        except (TypeError, ValueError) as exc:
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.FAILED,
                f"治理执行力化失败：{exc}",
                error_code="governance_execution_failed",
            )
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=report.summary_text(),
            data=report.public_dict(),
        )

    return governance_execution_adapter


def stable_governance_execution_digest(report: GovernanceExecutionReport) -> str:
    payload = report.public_dict()
    payload.pop("generated_at", None)
    payload.pop("report_digest", None)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _default_fast_lanes() -> list[GovernanceFastLane]:
    return [
        GovernanceFastLane(
            lane_ref="lane:a0_a2_read_analyze_plan",
            lane_name="A0-A2 只读分析与计划快车道",
            risk_levels=("A0", "A1", "A2"),
            action_kinds=("scan", "read", "diagnose", "planner_hint", "governance_projection"),
            planner_policy="默认允许生成分析、诊断、计划与治理投影；不因质量门失败阻断草案。",
            quality_gate_position="quality_gate_observes_draft_but_blocks_release_only",
        ),
        GovernanceFastLane(
            lane_ref="lane:a2_a3_draft_smoke_repair",
            lane_name="A2-A3 草案 / smoke / 最小修复快车道",
            risk_levels=("A2", "A3"),
            action_kinds=("tool_draft", "skill_draft", "patch_plan", "smoke_test", "targeted_regression"),
            planner_policy="允许生成最小草案、修复计划和 smoke 验证；正式写入、注册、激活另走护栏。",
            quality_gate_position="quality_gate_runs_before_delivery_or_activation",
        ),
        GovernanceFastLane(
            lane_ref="lane:a1_a4_resume_handoff_budget",
            lane_name="A1-A4 续接 / Handoff / 预算投影快车道",
            risk_levels=("A1", "A2", "A3", "A4"),
            action_kinds=("resume_plan", "handoff_digest", "budget_projection", "rollback_evidence"),
            planner_policy="允许把长链失败压成续接计划和投影；A4 真实副作用仍不直接执行。",
            quality_gate_position="quality_gate_blocks_release_not_resume_projection",
        ),
        GovernanceFastLane(
            lane_ref="lane:a2_a3_delivery_evidence",
            lane_name="A2-A3 交付证据快车道",
            risk_levels=("A2", "A3"),
            action_kinds=("change_set", "test_evidence", "manifest_evidence", "integrity_evidence"),
            planner_policy="允许整理交付证据、测试证据和完整性摘要；正式发布包仍走 Release Gate。",
            quality_gate_position="release_gate_after_evidence_before_publish",
        ),
    ]


def _build_boundaries(
    pending: list[dict[str, Any]],
    audit: list[dict[str, Any]],
    delivery: dict[str, Any],
    provider: dict[str, Any],
    notes: str,
) -> list[GovernanceBoundary]:
    boundaries = [
        GovernanceBoundary(
            boundary_ref="boundary:a5_hard_stop",
            boundary_name="A5 极高危硬边界",
            trigger="未知工具、越权路径、凭证读取、系统目录写入、危险命令、内核污染、裸调模型或外部副作用。",
            risk_level="A5",
            action="立即阻断；必要时要求用户确认并重新规划为低风险草案路径。",
            blocks_execution=True,
            requires_confirmation=True,
            hard_boundary=True,
        ),
        GovernanceBoundary(
            boundary_ref="boundary:release_activation_gate",
            boundary_name="正式发布 / 注册 / 激活护栏",
            trigger="create_release_bundle、正式 ZIP 发布、Tool/Skill 注册或激活、Provider 凭证绑定。",
            risk_level="A4",
            action="不阻断草案与 smoke；只在正式发布、注册、激活前要求质量门、审计和确认。",
            blocks_execution=False,
            requires_confirmation=True,
            quality_gate_required=True,
            release_or_activation_gate=True,
        ),
        GovernanceBoundary(
            boundary_ref="boundary:kernel_pollution_guard",
            boundary_name="tiangong_kernel 污染保护",
            trigger="任何新增、修改、删除 tiangong_kernel 文件或核心原语的行为。",
            risk_level="A5",
            action="保持硬拦或单独强确认；L6.30 外壳不得触碰内核。",
            blocks_execution=True,
            requires_confirmation=True,
            hard_boundary=True,
        ),
        GovernanceBoundary(
            boundary_ref="boundary:secret_provider_guard",
            boundary_name="密钥与 Provider 裸调保护",
            trigger="明文凭证、Provider SDK 直接调用、裸 HTTP 模型调用、跨层读取密钥。",
            risk_level="A5",
            action="阻断裸调与明文密钥；只允许声明式 ProviderProfile 与 L4/L5 受治理适配链。",
            blocks_execution=True,
            requires_confirmation=True,
            hard_boundary=True,
        ),
    ]
    if pending:
        boundaries.append(
            GovernanceBoundary(
                boundary_ref=_ref("boundary", "pending", len(pending)),
                boundary_name="待确认票据护栏",
                trigger=f"当前存在 {len(pending)} 个待确认票据。",
                risk_level="A4",
                action="Planner 可继续生成草案和复测计划，但真实副作用必须等票据解决。",
                blocks_execution=False,
                requires_confirmation=True,
                quality_gate_required=True,
                release_or_activation_gate=True,
            )
        )
    failed_audit = [item for item in audit if _safe_text(item.get("status") or item.get("result_status"), limit=80) in {"failed", "blocked", "confirmation_required"}]
    if failed_audit:
        boundaries.append(
            GovernanceBoundary(
                boundary_ref=_ref("boundary", "audit", len(failed_audit)),
                boundary_name="失败审计续接护栏",
                trigger=f"审计摘要中存在 {len(failed_audit)} 个失败/阻断/确认项。",
                risk_level="A3",
                action="优先进入恢复协调和最小回归，不扩大修复范围。",
                blocks_execution=False,
                quality_gate_required=True,
            )
        )
    if _safe_text(delivery.get("status"), limit=80) in {"delivery_standardization_ready", "ready"}:
        boundaries.append(
            GovernanceBoundary(
                boundary_ref="boundary:delivery_evidence_release_gate",
                boundary_name="交付证据发布护栏",
                trigger="交付证据已生成，但正式发布必须复核 manifest、sha256、integrity 和未做事项。",
                risk_level="A3",
                action="允许整理证据；发布前由 Release Gate 与质量门统一检查。",
                blocks_execution=False,
                quality_gate_required=True,
                release_or_activation_gate=True,
            )
        )
    if provider.get("schema"):
        boundaries.append(
            GovernanceBoundary(
                boundary_ref="boundary:provider_declarative_only",
                boundary_name="Provider 声明式适配护栏",
                trigger="ProviderProfile / CapabilityMatrix / API Surface 已存在。",
                risk_level="A4",
                action="保持声明式，不读取密钥、不触网、不注册正式 Adapter；真实调用走 L4/L5 治理链。",
                blocks_execution=False,
                requires_confirmation=True,
                quality_gate_required=True,
                release_or_activation_gate=True,
            )
        )
    if notes:
        boundaries.append(
            GovernanceBoundary(
                boundary_ref=_ref("boundary", "manual", notes),
                boundary_name="用户口径护栏",
                trigger=notes,
                risk_level="A2",
                action="按执行力第一压缩治理摩擦，同时保留 A5 硬边界。",
                blocks_execution=False,
            )
        )
    return boundaries


def _build_decisions(
    lanes: list[GovernanceFastLane],
    boundaries: list[GovernanceBoundary],
    recovery: dict[str, Any],
    learning: dict[str, Any],
    repair: dict[str, Any],
    delivery: dict[str, Any],
    provider: dict[str, Any],
    *,
    limit: int,
) -> list[GovernanceDecisionDraft]:
    decisions: list[GovernanceDecisionDraft] = []
    lane_lookup = {lane.lane_ref: lane for lane in lanes}
    def add(source: str, tool: str, risk: str, kind: str, lane_ref: str, reason: str, next_action: str) -> None:
        if len(decisions) >= limit:
            return
        status = "fast_pass_candidate" if risk in A0_A4_LEVELS and lane_ref in lane_lookup else "blocked"
        if any(bound.hard_boundary and risk == "A5" for bound in boundaries):
            status = "blocked"
        decisions.append(
            GovernanceDecisionDraft(
                decision_ref=_ref("decision", source, tool, risk, kind),
                source_ref=source,
                tool_or_action=tool,
                risk_level=risk,
                action_kind=kind,
                lane_ref=lane_ref,
                status=status,
                reason=reason,
                planner_next=next_action,
            )
        )

    for item in _as_dicts(learning.get("consumption_cards"))[:limit]:
        add(
            _safe_text(item.get("card_ref"), limit=120) or "learning:consumption_card",
            "build_learning_convergence",
            "A2",
            "planner_consumption_card",
            "lane:a0_a2_read_analyze_plan",
            "经验/Skill/Tool 合流结果可以直接作为 Planner 草案输入。",
            _safe_text(item.get("immediate_next_action"), limit=320) or "消费合流卡片并生成下一步计划。",
        )
    for item in _as_dicts(recovery.get("resume_plans"))[:limit]:
        add(
            _safe_text(item.get("plan_ref"), limit=120) or "recovery:resume_plan",
            "build_recovery_coordination",
            "A2",
            "resume_plan",
            "lane:a1_a4_resume_handoff_budget",
            "恢复协调结果用于续接，不直接执行补丁或派生子智能体。",
            _safe_text(item.get("next_action"), limit=320) or "按恢复计划续接。",
        )
    if repair.get("schema"):
        add(
            "project_repair:patch_plan",
            "build_project_repair_plan",
            "A2",
            "patch_plan",
            "lane:a2_a3_draft_smoke_repair",
            "PatchPlan 只生成修复计划，不直接写文件。",
            "先执行项目雷达/诊断，再用最小补丁计划和 targeted regression 验证。",
        )
    if delivery.get("schema"):
        add(
            "delivery_standardization:evidence",
            "build_delivery_standardization",
            "A2",
            "delivery_evidence",
            "lane:a2_a3_delivery_evidence",
            "交付证据可快速整理，正式发布仍走 Release Gate。",
            "整理 ChangeSet/TestEvidence/Manifest/Integrity/Todo 后再进入发布护栏。",
        )
    if provider.get("schema"):
        add(
            "provider_adaptation:declarative_profile",
            "build_provider_adaptation",
            "A4",
            "provider_declaration",
            "lane:a1_a4_resume_handoff_budget",
            "Provider 外壳只做声明式矩阵，不读取密钥、不触网。",
            "把模型能力作为 Planner 约束，真实调用交给 L4/L5 受治理链。",
        )
    for boundary in boundaries:
        if boundary.hard_boundary:
            decisions.append(
                GovernanceDecisionDraft(
                    decision_ref=_ref("decision", boundary.boundary_ref, boundary.risk_level),
                    source_ref=boundary.boundary_ref,
                    tool_or_action=boundary.boundary_name,
                    risk_level=boundary.risk_level,
                    action_kind="hard_boundary",
                    lane_ref="boundary:a5_hard_stop",
                    status="blocked",
                    reason=boundary.trigger,
                    planner_next=boundary.action,
                )
            )
            if len(decisions) >= limit:
                break
    return decisions[:limit]


def _build_planner_hints(
    decisions: list[GovernanceDecisionDraft],
    recovery: dict[str, Any],
    learning: dict[str, Any],
    repair: dict[str, Any],
    delivery: dict[str, Any],
    provider: dict[str, Any],
    shell: dict[str, Any],
    *,
    limit: int,
) -> list[PlannerGovernanceHint]:
    hints: list[PlannerGovernanceHint] = []
    for decision in decisions:
        if len(hints) >= limit:
            break
        if decision.status != "fast_pass_candidate":
            continue
        hints.append(
            PlannerGovernanceHint(
                hint_ref=_ref("gov_hint", decision.decision_ref),
                source_ref=decision.source_ref,
                title=f"治理快车道：{decision.action_kind}",
                next_action=decision.planner_next,
                lane_ref=decision.lane_ref,
                stop_condition="触发 A5、正式发布/注册/激活、凭证读取、内核路径或连续失败预算耗尽。",
            )
        )
    if not hints:
        hints.append(
            PlannerGovernanceHint(
                hint_ref="gov_hint:default_execution_first",
                source_ref="governance:l6_30_default",
                title="默认治理执行提示",
                next_action="优先生成可验证草案、smoke 和续接计划；只在 A5 或正式发布/注册/激活处停下。",
                lane_ref="lane:a0_a2_read_analyze_plan",
                stop_condition="A5 硬边界或 Release Gate 未满足。",
            )
        )
    if provider.get("schema") and len(hints) < limit:
        hints.append(
            PlannerGovernanceHint(
                hint_ref="gov_hint:provider_governed",
                source_ref="provider_adaptation:declarative_only",
                title="Provider 调用治理提示",
                next_action="Planner 只能消费 Provider 能力矩阵；真实模型调用必须经 Runtime/L4/L5 适配链。",
                lane_ref="lane:a1_a4_resume_handoff_budget",
                stop_condition="出现裸 SDK、明文凭证、跨层 HTTP 或未授权 Provider 调用。",
            )
        )
    if shell.get("schema") and len(hints) < limit:
        hints.append(
            PlannerGovernanceHint(
                hint_ref="gov_hint:shell_mount_preserve",
                source_ref="shell_mount:18_systems",
                title="18 系统壳装边界提示",
                next_action="继续把壳层输出压成 Planner 上下文，后续统一 Planner 接入时消费。",
                lane_ref="lane:a0_a2_read_analyze_plan",
                stop_condition="壳层变成真实注册/激活/执行通道。",
            )
        )
    return hints[:limit]


def _summary(
    lanes: list[GovernanceFastLane],
    boundaries: list[GovernanceBoundary],
    decisions: list[GovernanceDecisionDraft],
    hints: list[PlannerGovernanceHint],
    pending_count: int,
) -> str:
    hard = sum(1 for item in boundaries if item.hard_boundary)
    release = sum(1 for item in boundaries if item.release_or_activation_gate)
    fast = sum(1 for item in decisions if item.status == "fast_pass_candidate")
    blocked = sum(1 for item in decisions if item.status == "blocked")
    return (
        f"已把治理链压缩为执行护栏：fast_lane={len(lanes)}，boundary={len(boundaries)}，hard={hard}，"
        f"release_gate={release}，decision={len(decisions)}，fast_pass_candidate={fast}，blocked={blocked}，"
        f"planner_hint={len(hints)}，pending_confirmation={pending_count}。A0-A4 草案/分析/smoke/续接优先流转；"
        "A5、凭证、内核、裸调模型、正式发布/注册/激活仍受硬边界和质量门约束。"
    )


def _source_schemas(*reports: dict[str, Any]) -> list[str]:
    schemas: list[str] = []
    for report in reports:
        if isinstance(report, dict):
            schema = _safe_text(report.get("schema"), limit=180)
            if schema and schema not in schemas:
                schemas.append(schema)
    return schemas


def _safe_text(value: Any, *, limit: int = 500) -> str:
    text = "" if value is None else str(value)
    text = redact_text(text)
    text = SENSITIVE_PATTERN.sub("[REDACTED]", text)
    for word in SENSITIVE_WORDS:
        text = re.sub(re.escape(word), "[REDACTED]", text, flags=re.IGNORECASE)
    text = " ".join(text.split())
    return text[:limit]


def _as_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _ref(prefix: str, *parts: Any) -> str:
    payload = json.dumps([_safe_text(part, limit=240) for part in parts], ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}:{digest}"
