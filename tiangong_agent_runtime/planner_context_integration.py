"""L6.31 统一 Planner 接入 / 执行主链收口。

本模块把 L6.24-L6.30 已完成的外壳报告统一压缩为单一
``UnifiedPlannerContext``，让 LLM / Planner 每轮任务不用再手动读取一堆散报告。

边界：本模块只生成 Planner 可消费上下文、执行步骤草案和续接信封；不执行真实工具、
不注册正式 Tool/Skill/Provider、不读取密钥、不裸调模型、不修改 ``tiangong_kernel``。
执行力口径：A0-A4 草案 / 分析 / smoke / 续接进入快车道；A5、凭证、内核路径、
正式发布 / 注册 / 激活仍保留硬边界或确认护栏。
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

PLANNER_CONTEXT_INTEGRATION_SCHEMA = "tiangong.l6_31.planner_context_integration.v1"
SOURCE_VERSION = "L6.31-unified-planner-context"
A0_A4_LEVELS = {"A0", "A1", "A2", "A3", "A4"}
SENSITIVE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer|token|secret|password|credential)\s*[:=]\s*[^\s,;]+"
)
SENSITIVE_WORDS = ("api_key", "apikey", "authorization", "bearer", "token", "secret", "password", "credential")


@dataclass(frozen=True)
class PlannerSourceEvidence:
    """Planner 上下文输入源证据，只保留安全摘要和计数。"""

    source_ref: str
    source_name: str
    source_schema: str
    status: str
    item_count: int
    contributes_to: list[str] = field(default_factory=list)
    summary: str = ""

    def public_dict(self) -> dict[str, Any]:
        return {
            "source_ref": self.source_ref,
            "source_name": self.source_name,
            "source_schema": self.source_schema,
            "status": self.status,
            "item_count": self.item_count,
            "contributes_to": list(self.contributes_to),
            "summary": self.summary,
        }


@dataclass(frozen=True)
class UnifiedPlannerHint:
    """统一 Planner 提示。只给下一步方向，不触发真实执行。"""

    hint_ref: str
    source_ref: str
    title: str
    action_hint: str
    action_type: str
    risk_level: str = "A2"
    priority: str = "P1_execution"
    consumption_mode: str = "prepend_to_unified_planner_context"
    fast_lane_candidate: bool = True
    requires_confirmation: bool = False
    blocks_execution: bool = False
    stop_condition: str = "A5 / 正式发布 / 注册 / 激活 / 凭证读取 / 内核路径。"
    direct_execution_now: bool = False
    invokes_tool: bool = False
    registers_tool: bool = False
    registers_skill: bool = False
    touches_kernel: bool = False
    reads_secret: bool = False
    provider_call: bool = False

    def __post_init__(self) -> None:
        if self.direct_execution_now or self.invokes_tool:
            raise ValueError("L6.31 UnifiedPlannerHint cannot execute or invoke tools")
        forbidden = (self.registers_tool, self.registers_skill, self.touches_kernel, self.reads_secret, self.provider_call)
        if any(forbidden):
            raise ValueError("L6.31 UnifiedPlannerHint cannot register, touch kernel, read secrets or call providers")
        if self.risk_level == "A5" and not self.blocks_execution:
            raise ValueError("L6.31 A5 planner hint must be blocking")
        if self.blocks_execution and self.fast_lane_candidate:
            raise ValueError("L6.31 blocked planner hint cannot be fast-lane candidate")
        if self.requires_confirmation and self.fast_lane_candidate:
            raise ValueError("L6.31 confirmation hint cannot be fast-lane before confirmation")

    def public_dict(self) -> dict[str, Any]:
        return {
            "hint_ref": self.hint_ref,
            "source_ref": self.source_ref,
            "title": self.title,
            "action_hint": self.action_hint,
            "action_type": self.action_type,
            "risk_level": self.risk_level,
            "priority": self.priority,
            "consumption_mode": self.consumption_mode,
            "fast_lane_candidate": self.fast_lane_candidate,
            "requires_confirmation": self.requires_confirmation,
            "blocks_execution": self.blocks_execution,
            "stop_condition": self.stop_condition,
            "direct_execution_now": self.direct_execution_now,
            "invokes_tool": self.invokes_tool,
            "registers_tool": self.registers_tool,
            "registers_skill": self.registers_skill,
            "touches_kernel": self.touches_kernel,
            "reads_secret": self.reads_secret,
            "provider_call": self.provider_call,
        }


@dataclass(frozen=True)
class ExecutionStepDraft:
    """Planner 下一步执行草案。仍是草案，不执行。"""

    step_id: str
    title: str
    source_hint: str
    action_type: str
    risk_level: str
    requires_confirmation: bool
    suggested_tool_or_shell: str
    expected_evidence: str
    fallback_or_rollback: str
    fast_lane_candidate: bool = True
    direct_execution_now: bool = False
    applies_patch: bool = False
    writes_file: bool = False
    invokes_tool: bool = False
    touches_kernel: bool = False

    def __post_init__(self) -> None:
        if self.direct_execution_now or self.applies_patch or self.writes_file or self.invokes_tool or self.touches_kernel:
            raise ValueError("L6.31 ExecutionStepDraft must remain non-executing and non-mutating")
        if self.risk_level == "A5" and not self.requires_confirmation:
            raise ValueError("L6.31 A5 execution step must require confirmation or be blocked upstream")
        if self.requires_confirmation and self.fast_lane_candidate and self.risk_level == "A5":
            raise ValueError("L6.31 A5 execution step cannot be fast-lane candidate")

    def public_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "title": self.title,
            "source_hint": self.source_hint,
            "action_type": self.action_type,
            "risk_level": self.risk_level,
            "requires_confirmation": self.requires_confirmation,
            "suggested_tool_or_shell": self.suggested_tool_or_shell,
            "expected_evidence": self.expected_evidence,
            "fallback_or_rollback": self.fallback_or_rollback,
            "fast_lane_candidate": self.fast_lane_candidate,
            "direct_execution_now": self.direct_execution_now,
            "applies_patch": self.applies_patch,
            "writes_file": self.writes_file,
            "invokes_tool": self.invokes_tool,
            "touches_kernel": self.touches_kernel,
        }


@dataclass(frozen=True)
class PlannerResumeEnvelope:
    """长链续接信封。只保存下一轮可消费摘要。"""

    resume_mode: str
    last_known_state: str
    unresolved_failures: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    budget_hint: str = ""
    governance_hint: str = ""
    handoff_digest: str = ""
    ready_for_next_run: bool = True
    direct_execution_now: bool = False
    mutates_budget: bool = False
    spawns_agent: bool = False
    touches_kernel: bool = False

    def __post_init__(self) -> None:
        if not self.ready_for_next_run:
            raise ValueError("L6.31 PlannerResumeEnvelope must be ready for next run")
        if self.direct_execution_now or self.mutates_budget or self.spawns_agent or self.touches_kernel:
            raise ValueError("L6.31 PlannerResumeEnvelope cannot execute, mutate budget, spawn agent or touch kernel")

    def public_dict(self) -> dict[str, Any]:
        return {
            "resume_mode": self.resume_mode,
            "last_known_state": self.last_known_state,
            "unresolved_failures": list(self.unresolved_failures),
            "next_steps": list(self.next_steps),
            "budget_hint": self.budget_hint,
            "governance_hint": self.governance_hint,
            "handoff_digest": self.handoff_digest,
            "ready_for_next_run": self.ready_for_next_run,
            "direct_execution_now": self.direct_execution_now,
            "mutates_budget": self.mutates_budget,
            "spawns_agent": self.spawns_agent,
            "touches_kernel": self.touches_kernel,
        }


@dataclass(frozen=True)
class UnifiedPlannerContext:
    """统一 Planner 消费对象。"""

    task_id: str
    run_id: str
    source_version: str
    active_shell_systems: list[str] = field(default_factory=list)
    source_evidence: list[PlannerSourceEvidence] = field(default_factory=list)
    planner_hints: list[UnifiedPlannerHint] = field(default_factory=list)
    risk_boundaries: list[dict[str, Any]] = field(default_factory=list)
    fast_lane_actions: list[dict[str, Any]] = field(default_factory=list)
    blocked_actions: list[dict[str, Any]] = field(default_factory=list)
    required_confirmations: list[dict[str, Any]] = field(default_factory=list)
    regression_targets: list[dict[str, Any]] = field(default_factory=list)
    delivery_requirements: list[dict[str, Any]] = field(default_factory=list)
    recovery_resume_plan: PlannerResumeEnvelope | None = None
    provider_surface_options: list[dict[str, Any]] = field(default_factory=list)
    learning_consumption_cards: list[dict[str, Any]] = field(default_factory=list)
    next_execution_steps: list[ExecutionStepDraft] = field(default_factory=list)
    execution_first: bool = True
    shell_only: bool = True
    unified_entrypoint: bool = True
    planner_consumable: bool = True
    a0_a4_fast_lane_preserved: bool = True
    a5_hard_boundary_preserved: bool = True
    no_direct_execution: bool = True
    no_registry_mutation: bool = True
    no_kernel_mutation: bool = True
    no_secret_read: bool = True
    no_provider_call: bool = True

    def __post_init__(self) -> None:
        required = (
            self.execution_first,
            self.shell_only,
            self.unified_entrypoint,
            self.planner_consumable,
            self.a0_a4_fast_lane_preserved,
            self.a5_hard_boundary_preserved,
            self.no_direct_execution,
            self.no_registry_mutation,
            self.no_kernel_mutation,
            self.no_secret_read,
            self.no_provider_call,
        )
        if not all(required):
            raise ValueError("L6.31 UnifiedPlannerContext must remain execution-first, shell-only and non-mutating")
        if any(step.direct_execution_now or step.touches_kernel for step in self.next_execution_steps):
            raise ValueError("L6.31 UnifiedPlannerContext cannot contain executing or kernel-touching steps")
        if any(hint.risk_level == "A5" and hint.fast_lane_candidate for hint in self.planner_hints):
            raise ValueError("L6.31 UnifiedPlannerContext cannot fast-lane A5 hints")

    def public_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "run_id": self.run_id,
            "source_version": self.source_version,
            "active_shell_systems": list(self.active_shell_systems),
            "active_shell_system_count": len(self.active_shell_systems),
            "source_evidence": [item.public_dict() for item in self.source_evidence],
            "planner_hints": [item.public_dict() for item in self.planner_hints],
            "risk_boundaries": list(self.risk_boundaries),
            "fast_lane_actions": list(self.fast_lane_actions),
            "blocked_actions": list(self.blocked_actions),
            "required_confirmations": list(self.required_confirmations),
            "regression_targets": list(self.regression_targets),
            "delivery_requirements": list(self.delivery_requirements),
            "recovery_resume_plan": self.recovery_resume_plan.public_dict() if self.recovery_resume_plan else None,
            "provider_surface_options": list(self.provider_surface_options),
            "learning_consumption_cards": list(self.learning_consumption_cards),
            "next_execution_steps": [item.public_dict() for item in self.next_execution_steps],
            "planner_hint_count": len(self.planner_hints),
            "source_evidence_count": len(self.source_evidence),
            "risk_boundary_count": len(self.risk_boundaries),
            "fast_lane_action_count": len(self.fast_lane_actions),
            "blocked_action_count": len(self.blocked_actions),
            "required_confirmation_count": len(self.required_confirmations),
            "regression_target_count": len(self.regression_targets),
            "delivery_requirement_count": len(self.delivery_requirements),
            "provider_surface_option_count": len(self.provider_surface_options),
            "learning_consumption_card_count": len(self.learning_consumption_cards),
            "next_execution_step_count": len(self.next_execution_steps),
            "execution_first": self.execution_first,
            "shell_only": self.shell_only,
            "unified_entrypoint": self.unified_entrypoint,
            "planner_consumable": self.planner_consumable,
            "a0_a4_fast_lane_preserved": self.a0_a4_fast_lane_preserved,
            "a5_hard_boundary_preserved": self.a5_hard_boundary_preserved,
            "no_direct_execution": self.no_direct_execution,
            "no_registry_mutation": self.no_registry_mutation,
            "no_kernel_mutation": self.no_kernel_mutation,
            "no_secret_read": self.no_secret_read,
            "no_provider_call": self.no_provider_call,
        }


@dataclass(frozen=True)
class PlannerContextReport:
    """L6.31 统一 Planner 上下文报告。"""

    schema: str
    generated_at: float
    status: str
    summary: str
    unified_context: UnifiedPlannerContext
    source_schemas: list[str] = field(default_factory=list)
    notes_used: bool = False
    report_digest: str = ""
    execution_first: bool = True
    shell_only: bool = True
    unified_entrypoint: bool = True
    planner_consumable: bool = True
    a0_a4_fast_lane_preserved: bool = True
    a5_hard_boundary_preserved: bool = True
    provider_declaration_only: bool = True
    budget_projection_only: bool = True
    recovery_projection_only: bool = True
    no_direct_execution: bool = True
    no_registry_mutation: bool = True
    no_kernel_mutation: bool = True
    no_secret_read: bool = True
    no_provider_call: bool = True
    invokes_tool: bool = False
    applies_patch: bool = False
    writes_file: bool = False
    mutates_budget: bool = False
    registers_tool: bool = False
    registers_skill: bool = False
    registers_provider: bool = False
    touches_kernel: bool = False
    reads_secret: bool = False
    calls_provider: bool = False

    def __post_init__(self) -> None:
        required = (
            self.execution_first,
            self.shell_only,
            self.unified_entrypoint,
            self.planner_consumable,
            self.a0_a4_fast_lane_preserved,
            self.a5_hard_boundary_preserved,
            self.provider_declaration_only,
            self.budget_projection_only,
            self.recovery_projection_only,
            self.no_direct_execution,
            self.no_registry_mutation,
            self.no_kernel_mutation,
            self.no_secret_read,
            self.no_provider_call,
        )
        if not all(required):
            raise ValueError("L6.31 PlannerContextReport must remain shell-only and non-mutating")
        forbidden = (
            self.invokes_tool,
            self.applies_patch,
            self.writes_file,
            self.mutates_budget,
            self.registers_tool,
            self.registers_skill,
            self.registers_provider,
            self.touches_kernel,
            self.reads_secret,
            self.calls_provider,
        )
        if any(forbidden):
            raise ValueError("L6.31 PlannerContextReport cannot execute, mutate, register, read secrets or call providers")

    @property
    def source_evidence_count(self) -> int:
        return len(self.unified_context.source_evidence)

    @property
    def planner_hint_count(self) -> int:
        return len(self.unified_context.planner_hints)

    @property
    def next_execution_step_count(self) -> int:
        return len(self.unified_context.next_execution_steps)

    @property
    def fast_lane_action_count(self) -> int:
        return len(self.unified_context.fast_lane_actions)

    @property
    def blocked_action_count(self) -> int:
        return len(self.unified_context.blocked_actions)

    @property
    def required_confirmation_count(self) -> int:
        return len(self.unified_context.required_confirmations)

    @property
    def active_shell_system_count(self) -> int:
        return len(self.unified_context.active_shell_systems)

    @property
    def regression_target_count(self) -> int:
        return len(self.unified_context.regression_targets)

    @property
    def delivery_requirement_count(self) -> int:
        return len(self.unified_context.delivery_requirements)

    @property
    def provider_surface_option_count(self) -> int:
        return len(self.unified_context.provider_surface_options)

    @property
    def learning_consumption_card_count(self) -> int:
        return len(self.unified_context.learning_consumption_cards)

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "status": self.status,
            "summary": self.summary,
            "unified_context": self.unified_context.public_dict(),
            "source_schemas": list(self.source_schemas),
            "notes_used": self.notes_used,
            "source_evidence_count": self.source_evidence_count,
            "planner_hint_count": self.planner_hint_count,
            "next_execution_step_count": self.next_execution_step_count,
            "fast_lane_action_count": self.fast_lane_action_count,
            "blocked_action_count": self.blocked_action_count,
            "required_confirmation_count": self.required_confirmation_count,
            "active_shell_system_count": self.active_shell_system_count,
            "regression_target_count": self.regression_target_count,
            "delivery_requirement_count": self.delivery_requirement_count,
            "provider_surface_option_count": self.provider_surface_option_count,
            "learning_consumption_card_count": self.learning_consumption_card_count,
            "execution_first": self.execution_first,
            "shell_only": self.shell_only,
            "unified_entrypoint": self.unified_entrypoint,
            "planner_consumable": self.planner_consumable,
            "a0_a4_fast_lane_preserved": self.a0_a4_fast_lane_preserved,
            "a5_hard_boundary_preserved": self.a5_hard_boundary_preserved,
            "provider_declaration_only": self.provider_declaration_only,
            "budget_projection_only": self.budget_projection_only,
            "recovery_projection_only": self.recovery_projection_only,
            "no_direct_execution": self.no_direct_execution,
            "no_registry_mutation": self.no_registry_mutation,
            "no_kernel_mutation": self.no_kernel_mutation,
            "no_secret_read": self.no_secret_read,
            "no_provider_call": self.no_provider_call,
            "invokes_tool": self.invokes_tool,
            "applies_patch": self.applies_patch,
            "writes_file": self.writes_file,
            "mutates_budget": self.mutates_budget,
            "registers_tool": self.registers_tool,
            "registers_skill": self.registers_skill,
            "registers_provider": self.registers_provider,
            "touches_kernel": self.touches_kernel,
            "reads_secret": self.reads_secret,
            "calls_provider": self.calls_provider,
            "report_digest": self.report_digest,
        }

    def summary_text(self) -> str:
        return (
            "L6.31 统一 Planner 接入："
            f"status={self.status}；sources={self.source_evidence_count}；hints={self.planner_hint_count}；"
            f"steps={self.next_execution_step_count}；fast_lane={self.fast_lane_action_count}；"
            f"blocked={self.blocked_action_count}；confirmations={self.required_confirmation_count}；"
            f"active_shell={self.active_shell_system_count}。{self.summary}"
        )

    def markdown_report(self) -> str:
        ctx = self.unified_context
        lines = [
            "# 临渊者 L6.31 统一 Planner 接入报告",
            "",
            f"- schema: `{self.schema}`",
            f"- status: `{self.status}`",
            f"- unified_entrypoint: `{self.unified_entrypoint}`",
            f"- planner_consumable: `{self.planner_consumable}`",
            f"- report_digest: `{self.report_digest}`",
            "",
            "## 摘要",
            "",
            self.summary,
            "",
            "## 下一步执行草案",
            "",
        ]
        for step in ctx.next_execution_steps:
            lines.append(f"- `{step.step_id}` [{step.risk_level}] {step.title}: {step.suggested_tool_or_shell}")
        lines.extend(["", "## 风险边界", ""])
        for item in ctx.risk_boundaries[:12]:
            lines.append(f"- `{item.get('boundary_ref', item.get('source_ref', '<unknown>'))}` {item.get('risk_level', '')}: {item.get('action', item.get('title', ''))}")
        lines.append("")
        lines.append("> L6.31 只生成统一 Planner 上下文；真实执行、写入、注册、Provider 调用仍回到 Runtime / L4 / L5 治理链。")
        return "\n".join(lines)


class PlannerContextIntegrationBridge:
    """Runtime 外壳层统一 Planner 上下文桥。"""

    def __init__(self) -> None:
        self._last_report: PlannerContextReport | None = None

    @property
    def last_report(self) -> PlannerContextReport | None:
        return self._last_report

    def reset(self) -> None:
        self._last_report = None

    def build(
        self,
        *,
        shell_mount_report: dict[str, Any] | None = None,
        project_repair_report: dict[str, Any] | None = None,
        delivery_standardization_report: dict[str, Any] | None = None,
        provider_adaptation_report: dict[str, Any] | None = None,
        learning_convergence_report: dict[str, Any] | None = None,
        recovery_coordination_report: dict[str, Any] | None = None,
        governance_execution_report: dict[str, Any] | None = None,
        task_id: str = "default_task",
        run_id: str = "default_run",
        notes: str = "",
        max_items: int = 16,
    ) -> PlannerContextReport:
        limit = max(1, min(int(max_items), 60))
        safe_notes = _safe_text(notes, limit=700)
        shell = shell_mount_report or {}
        repair = project_repair_report or {}
        delivery = delivery_standardization_report or {}
        provider = provider_adaptation_report or {}
        learning = learning_convergence_report or {}
        recovery = recovery_coordination_report or {}
        governance = governance_execution_report or {}

        sources = _build_source_evidence(shell, repair, delivery, provider, learning, recovery, governance)
        active_shell_systems = _active_shell_systems(shell, limit=limit)
        provider_options = _provider_options(provider, limit=limit)
        learning_cards = _safe_dict_list(learning.get("consumption_cards"), limit=limit)
        regression_targets = _regression_targets(repair, delivery, limit=limit)
        delivery_requirements = _delivery_requirements(delivery, limit=limit)
        risk_boundaries = _risk_boundaries(governance, provider, limit=limit)
        fast_lane_actions = _fast_lane_actions(governance, limit=limit)
        blocked_actions = _blocked_actions(governance, risk_boundaries, limit=limit)
        required_confirmations = _required_confirmations(governance, risk_boundaries, limit=limit)
        resume_envelope = _resume_envelope(recovery, governance, safe_notes, limit=limit)
        hints = _planner_hints(shell, repair, delivery, provider, learning, recovery, governance, risk_boundaries, limit=limit)
        steps = _execution_steps(hints, regression_targets, delivery_requirements, limit=limit)
        source_schemas = _source_schemas(shell, repair, delivery, provider, learning, recovery, governance)
        status = "planner_context_ready" if hints and steps else "planner_context_partial"
        summary = _summary(
            sources=sources,
            hints=hints,
            steps=steps,
            fast_lane_actions=fast_lane_actions,
            blocked_actions=blocked_actions,
            confirmations=required_confirmations,
            notes=safe_notes,
        )
        context = UnifiedPlannerContext(
            task_id=_safe_text(task_id, limit=160) or "default_task",
            run_id=_safe_text(run_id, limit=160) or _ref("run", task_id, time()),
            source_version=SOURCE_VERSION,
            active_shell_systems=active_shell_systems,
            source_evidence=sources,
            planner_hints=hints,
            risk_boundaries=risk_boundaries,
            fast_lane_actions=fast_lane_actions,
            blocked_actions=blocked_actions,
            required_confirmations=required_confirmations,
            regression_targets=regression_targets,
            delivery_requirements=delivery_requirements,
            recovery_resume_plan=resume_envelope,
            provider_surface_options=provider_options,
            learning_consumption_cards=learning_cards,
            next_execution_steps=steps,
        )
        report = PlannerContextReport(
            schema=PLANNER_CONTEXT_INTEGRATION_SCHEMA,
            generated_at=time(),
            status=status,
            summary=summary,
            unified_context=context,
            source_schemas=source_schemas,
            notes_used=bool(safe_notes),
        )
        report = PlannerContextReport(**{**report.__dict__, "report_digest": stable_planner_context_digest(report)})
        self._last_report = report
        return report

    def public_dict(self) -> dict[str, Any]:
        if self._last_report is None:
            return {
                "schema": PLANNER_CONTEXT_INTEGRATION_SCHEMA,
                "status": "empty",
                "message": "暂无 L6.31 统一 Planner 上下文，请先执行 /planner-context-build。",
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
        ctx = report.unified_context
        next_steps = "; ".join(item.title for item in ctx.next_execution_steps[:4]) or "无"
        return (
            "最近 L6.31 统一 Planner 上下文："
            f"status={report.status}; sources={report.source_evidence_count}; hints={report.planner_hint_count}; "
            f"steps={report.next_execution_step_count}; fast_lane={report.fast_lane_action_count}; "
            f"blocked={report.blocked_action_count}; a5_hard_boundary=True; unified_entrypoint=True; "
            f"next={next_steps}; shell_only=True; no_direct_execution=True; no_kernel_mutation=True"
        )[:1800]



def build_planner_context_integration_adapter(
    bridge: PlannerContextIntegrationBridge,
    shell_mount: Any,
    project_repair: Any,
    delivery_standardization: Any,
    provider_adaptation: Any,
    learning_convergence: Any,
    recovery_coordination: Any,
    governance_execution: Any,
):
    def planner_context_integration_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            report = bridge.build(
                shell_mount_report=shell_mount.public_dict(),
                project_repair_report=project_repair.public_dict(),
                delivery_standardization_report=delivery_standardization.public_dict(),
                provider_adaptation_report=provider_adaptation.public_dict(),
                learning_convergence_report=learning_convergence.public_dict(),
                recovery_coordination_report=recovery_coordination.public_dict(),
                governance_execution_report=governance_execution.public_dict(),
                task_id=str(invocation.arguments.get("task_id") or invocation.arguments.get("task") or "runtime_task"),
                run_id=str(invocation.arguments.get("run_id") or getattr(context, "run_id", context.turn_id)),
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
                max_items=int(invocation.arguments.get("max_items") or 16),
            )
        except (TypeError, ValueError) as exc:
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.FAILED,
                f"统一 Planner 上下文构建失败：{exc}",
                error_code="planner_context_integration_failed",
            )
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=report.summary_text(),
            data=report.public_dict(),
        )

    return planner_context_integration_adapter



def stable_planner_context_digest(report: PlannerContextReport) -> str:
    payload = report.public_dict()
    payload.pop("generated_at", None)
    payload.pop("report_digest", None)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]



def _build_source_evidence(*reports: dict[str, Any]) -> list[PlannerSourceEvidence]:
    names = (
        "shell_mount",
        "project_repair",
        "delivery_standardization",
        "provider_adaptation",
        "learning_convergence",
        "recovery_coordination",
        "governance_execution",
    )
    contributes = {
        "shell_mount": ["active_shell_systems", "system_mount_map"],
        "project_repair": ["patch_plan", "regression_targets", "rollback_hint"],
        "delivery_standardization": ["delivery_requirements", "test_evidence", "todo_report"],
        "provider_adaptation": ["provider_surface_options", "governance_mounts"],
        "learning_convergence": ["planner_hints", "learning_consumption_cards"],
        "recovery_coordination": ["recovery_resume_plan", "budget_hint", "handoff_digest"],
        "governance_execution": ["risk_boundaries", "fast_lane_actions", "required_confirmations"],
    }
    evidence: list[PlannerSourceEvidence] = []
    for name, report in zip(names, reports):
        if not isinstance(report, dict):
            report = {}
        schema = _safe_text(report.get("schema"), limit=200)
        status = _safe_text(report.get("status"), limit=120) or "empty"
        if not schema:
            schema = f"tiangong.unknown.{name}.v0"
        item_count = _count_report_items(name, report)
        evidence.append(
            PlannerSourceEvidence(
                source_ref=_ref("source", name, schema, status),
                source_name=name,
                source_schema=schema,
                status=status,
                item_count=item_count,
                contributes_to=contributes.get(name, []),
                summary=_safe_text(report.get("summary") or report.get("message"), limit=360),
            )
        )
    return evidence



def _count_report_items(name: str, report: dict[str, Any]) -> int:
    if not report or report.get("status") == "empty":
        return 0
    if name == "shell_mount":
        return int(report.get("system_count") or len(_as_dicts(report.get("systems"))))
    if name == "project_repair":
        return len(_as_dicts(report.get("patch_plan"))) + len(_as_dicts(report.get("regression_hints"))) + (1 if report.get("rollback_evidence") else 0)
    if name == "delivery_standardization":
        return len(_as_dicts(report.get("change_set"))) + len(_as_dicts(report.get("test_evidence"))) + len(_as_dicts(report.get("todo_report")))
    if name == "provider_adaptation":
        return len(_as_dicts(report.get("provider_profiles"))) + len(_as_dicts(report.get("api_surface_routes"))) + len(_as_dicts(report.get("governance_mounts")))
    if name == "learning_convergence":
        return len(_as_dicts(report.get("planner_hint_routes"))) + len(_as_dicts(report.get("consumption_cards")))
    if name == "recovery_coordination":
        return len(_as_dicts(report.get("failure_signals"))) + len(_as_dicts(report.get("resume_plans"))) + len(_as_dicts(report.get("handoff_digests")))
    if name == "governance_execution":
        return len(_as_dicts(report.get("planner_hints"))) + len(_as_dicts(report.get("boundaries"))) + len(_as_dicts(report.get("decisions")))
    return 0



def _active_shell_systems(shell: dict[str, Any], *, limit: int) -> list[str]:
    systems = []
    for item in _as_dicts(shell.get("systems")):
        status = _safe_text(item.get("status"), limit=120)
        if status in {"active_shell_mounted", "partial_shell_mounted"}:
            system_id = _safe_text(item.get("system_id"), limit=60)
            name = _safe_text(item.get("name"), limit=160)
            systems.append(f"{system_id}:{name}" if name else system_id)
    return systems[:limit]



def _provider_options(provider: dict[str, Any], *, limit: int) -> list[dict[str, Any]]:
    options: list[dict[str, Any]] = []
    for item in _as_dicts(provider.get("api_surface_routes"))[:limit]:
        options.append(
            _safe_payload(
                {
                    "provider_id": item.get("provider_id"),
                    "surface_id": item.get("surface_id"),
                    "route_kind": item.get("route_kind"),
                    "endpoint_ref": item.get("endpoint_ref"),
                    "credential_scope_ref": item.get("credential_scope_ref"),
                    "live_call_enabled": False,
                    "planner_use": "declarative_candidate_only",
                }
            )
        )
    return options



def _regression_targets(repair: dict[str, Any], delivery: dict[str, Any], *, limit: int) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for item in _as_dicts(repair.get("regression_hints")):
        targets.append(
            _safe_payload(
                {
                    "source_ref": item.get("name") or item.get("hint_ref") or "project_repair:regression_hint",
                    "command": item.get("command"),
                    "target": item.get("target"),
                    "priority": item.get("priority", "P1"),
                    "reason": item.get("reason"),
                    "runs_now": False,
                }
            )
        )
        if len(targets) >= limit:
            return targets
    for item in _as_dicts(delivery.get("test_evidence")):
        targets.append(
            _safe_payload(
                {
                    "source_ref": item.get("test_ref") or item.get("name") or "delivery:test_evidence",
                    "command": item.get("command"),
                    "target": item.get("target"),
                    "status": item.get("status"),
                    "reason": "交付证据链要求保留测试状态并在正式交付前复核。",
                    "runs_now": False,
                }
            )
        )
        if len(targets) >= limit:
            return targets
    return targets



def _delivery_requirements(delivery: dict[str, Any], *, limit: int) -> list[dict[str, Any]]:
    requirements: list[dict[str, Any]] = []
    for item in _as_dicts(delivery.get("todo_report")):
        requirements.append(
            _safe_payload(
                {
                    "requirement_ref": item.get("item_id") or _ref("todo", item),
                    "priority": item.get("priority", "P1"),
                    "description": item.get("description"),
                    "reason": item.get("reason"),
                    "owner_systems": item.get("owner_systems") or [],
                }
            )
        )
        if len(requirements) >= limit:
            return requirements
    manifest = delivery.get("manifest_evidence") if isinstance(delivery.get("manifest_evidence"), dict) else {}
    integrity = delivery.get("integrity_evidence") if isinstance(delivery.get("integrity_evidence"), dict) else {}
    if manifest:
        requirements.append(
            _safe_payload(
                {
                    "requirement_ref": "delivery:manifest_evidence",
                    "priority": "P0",
                    "description": "正式交付前必须有 manifest 证据。",
                    "status": manifest.get("status"),
                    "manifest_available": manifest.get("manifest_available"),
                }
            )
        )
    if integrity and len(requirements) < limit:
        requirements.append(
            _safe_payload(
                {
                    "requirement_ref": "delivery:integrity_evidence",
                    "priority": "P0",
                    "description": "正式交付前必须有 sha256 / integrity 证据。",
                    "status": integrity.get("status"),
                    "report_digest": integrity.get("report_digest"),
                }
            )
        )
    return requirements[:limit]



def _risk_boundaries(governance: dict[str, Any], provider: dict[str, Any], *, limit: int) -> list[dict[str, Any]]:
    boundaries: list[dict[str, Any]] = []
    for item in _as_dicts(governance.get("boundaries"))[:limit]:
        boundaries.append(_safe_payload({**item, "source_ref": item.get("boundary_ref") or "governance:boundary"}))
    if not any(item.get("risk_level") == "A5" for item in boundaries):
        boundaries.append(
            {
                "source_ref": "boundary:a5_default_hard_stop",
                "boundary_ref": "boundary:a5_default_hard_stop",
                "boundary_name": "默认 A5 硬边界",
                "trigger": "A5、凭证读取、内核路径、裸调模型、越权外部副作用。",
                "risk_level": "A5",
                "action": "阻断并要求重新规划或人工确认。",
                "blocks_execution": True,
                "hard_boundary": True,
            }
        )
    if provider.get("schema") and len(boundaries) < limit:
        boundaries.append(
            {
                "source_ref": "boundary:provider_declarative_only",
                "boundary_ref": "boundary:provider_declarative_only",
                "boundary_name": "Provider 声明式边界",
                "trigger": "出现 Provider SDK 裸调、明文密钥或 L6 插件直连网络。",
                "risk_level": "A5",
                "action": "禁止 L6 直连；交给 L4/L5 Runtime 治理链。",
                "blocks_execution": True,
                "hard_boundary": True,
            }
        )
    return boundaries[:limit]



def _fast_lane_actions(governance: dict[str, Any], *, limit: int) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for item in _as_dicts(governance.get("fast_lanes"))[:limit]:
        actions.append(
            _safe_payload(
                {
                    "lane_ref": item.get("lane_ref"),
                    "lane_name": item.get("lane_name"),
                    "risk_levels": item.get("risk_levels") or [],
                    "action_kinds": item.get("action_kinds") or [],
                    "planner_policy": item.get("planner_policy"),
                    "quality_gate_position": item.get("quality_gate_position"),
                    "direct_execution_now": False,
                }
            )
        )
    for item in _as_dicts(governance.get("decisions")):
        if len(actions) >= limit:
            break
        if item.get("status") == "fast_pass_candidate":
            actions.append(
                _safe_payload(
                    {
                        "decision_ref": item.get("decision_ref"),
                        "source_ref": item.get("source_ref"),
                        "action_kind": item.get("action_kind"),
                        "risk_level": item.get("risk_level"),
                        "planner_next": item.get("planner_next"),
                        "direct_execution_now": False,
                    }
                )
            )
    return actions[:limit]



def _blocked_actions(governance: dict[str, Any], boundaries: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    blocked: list[dict[str, Any]] = []
    for item in _as_dicts(governance.get("decisions")):
        if item.get("status") == "blocked":
            blocked.append(
                _safe_payload(
                    {
                        "decision_ref": item.get("decision_ref"),
                        "source_ref": item.get("source_ref"),
                        "risk_level": item.get("risk_level"),
                        "action_kind": item.get("action_kind"),
                        "reason": item.get("reason"),
                        "planner_next": item.get("planner_next"),
                    }
                )
            )
        if len(blocked) >= limit:
            return blocked
    for item in boundaries:
        if len(blocked) >= limit:
            break
        if item.get("blocks_execution") or item.get("hard_boundary"):
            blocked.append(
                _safe_payload(
                    {
                        "boundary_ref": item.get("boundary_ref") or item.get("source_ref"),
                        "risk_level": item.get("risk_level"),
                        "reason": item.get("trigger"),
                        "planner_next": item.get("action"),
                    }
                )
            )
    return blocked[:limit]



def _required_confirmations(governance: dict[str, Any], boundaries: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    confirmations: list[dict[str, Any]] = []
    for item in _as_dicts(governance.get("decisions")):
        if item.get("status") == "confirmation_required":
            confirmations.append(_safe_payload({**item, "source_ref": item.get("source_ref") or "governance:decision"}))
        if len(confirmations) >= limit:
            return confirmations
    for item in boundaries:
        if len(confirmations) >= limit:
            break
        if item.get("requires_confirmation") or item.get("release_or_activation_gate"):
            confirmations.append(
                _safe_payload(
                    {
                        "boundary_ref": item.get("boundary_ref") or item.get("source_ref"),
                        "risk_level": item.get("risk_level"),
                        "required_for": item.get("boundary_name") or item.get("action"),
                        "reason": item.get("trigger"),
                    }
                )
            )
    pending = int(governance.get("pending_confirmation_count") or 0)
    if pending and len(confirmations) < limit:
        confirmations.append(
            {
                "confirmation_ref": "governance:pending_confirmation_count",
                "pending_confirmation_count": pending,
                "reason": "已有待确认票据，统一 Planner 只能提示，不能自动确认。",
            }
        )
    return confirmations[:limit]



def _resume_envelope(recovery: dict[str, Any], governance: dict[str, Any], notes: str, *, limit: int) -> PlannerResumeEnvelope:
    failures = [_safe_text(item.get("summary") or item.get("error_code") or item.get("status"), limit=220) for item in _as_dicts(recovery.get("failure_signals"))[:limit]]
    plans = _as_dicts(recovery.get("resume_plans"))[:limit]
    next_steps: list[str] = []
    for plan in plans:
        next_action = _safe_text(plan.get("next_action"), limit=260)
        if next_action:
            next_steps.append(next_action)
        for ordered in plan.get("ordered_steps") or []:
            if len(next_steps) >= limit:
                break
            next_steps.append(_safe_text(ordered, limit=220))
    if not next_steps:
        next_steps = ["先读取 UnifiedPlannerContext，再按 next_execution_steps 生成最小执行计划。"]
    budgets = _as_dicts(recovery.get("budget_updates"))
    budget_hint = "；".join(
        _safe_text(
            f"{item.get('budget_pool', 'default')} remaining={item.get('remaining_step_hint', 'unknown')} policy={item.get('continuation_policy', '')}",
            limit=220,
        )
        for item in budgets[:3]
    )
    governance_hint = "；".join(
        _safe_text(item.get("next_action") or item.get("planner_next") or item.get("title"), limit=220)
        for item in (_as_dicts(governance.get("planner_hints")) + _as_dicts(governance.get("decisions")))[:3]
    )
    handoff_digest = "；".join(
        _safe_text(item.get("task_boundary") or item.get("summary") or item.get("handoff_ref"), limit=220)
        for item in _as_dicts(recovery.get("handoff_digests"))[:3]
    )
    last_known = _safe_text(recovery.get("summary"), limit=360) or _safe_text(governance.get("summary"), limit=360)
    if notes:
        last_known = (last_known + f"；备注：{notes}").strip("；")
    return PlannerResumeEnvelope(
        resume_mode="l6_31_unified_context_resume",
        last_known_state=last_known or "已生成统一 Planner 上下文，可进入下一轮执行规划。",
        unresolved_failures=[item for item in failures if item][:limit],
        next_steps=next_steps[:limit],
        budget_hint=budget_hint,
        governance_hint=governance_hint,
        handoff_digest=handoff_digest,
    )



def _planner_hints(
    shell: dict[str, Any],
    repair: dict[str, Any],
    delivery: dict[str, Any],
    provider: dict[str, Any],
    learning: dict[str, Any],
    recovery: dict[str, Any],
    governance: dict[str, Any],
    boundaries: list[dict[str, Any]],
    *,
    limit: int,
) -> list[UnifiedPlannerHint]:
    hints: list[UnifiedPlannerHint] = []

    def add(
        *,
        source_ref: str,
        title: str,
        action_hint: str,
        action_type: str,
        risk_level: str = "A2",
        priority: str = "P1_execution",
        fast_lane: bool = True,
        requires_confirmation: bool = False,
        blocks_execution: bool = False,
        stop_condition: str = "A5 / 正式发布 / 注册 / 激活 / 凭证读取 / 内核路径。",
    ) -> None:
        if len(hints) >= limit:
            return
        if blocks_execution or requires_confirmation:
            fast_lane = False
        hints.append(
            UnifiedPlannerHint(
                hint_ref=_ref("planner_hint", source_ref, title, action_type),
                source_ref=_safe_text(source_ref, limit=160),
                title=_safe_text(title, limit=180),
                action_hint=_safe_text(action_hint, limit=420),
                action_type=_safe_text(action_type, limit=100),
                risk_level=_safe_text(risk_level, limit=20) or "A2",
                priority=_safe_text(priority, limit=80),
                fast_lane_candidate=fast_lane,
                requires_confirmation=requires_confirmation,
                blocks_execution=blocks_execution,
                stop_condition=_safe_text(stop_condition, limit=360),
            )
        )

    for item in _as_dicts(learning.get("consumption_cards")):
        add(
            source_ref=item.get("card_ref") or "learning:consumption_card",
            title=item.get("title") or "消费经验 / Skill / Tool 合流卡片",
            action_hint=item.get("immediate_next_action") or "把合流卡片直接放入下一轮 Planner 输入。",
            action_type="learning_consumption_card",
            risk_level="A2",
            priority="P0_execution",
        )
    for item in _as_dicts(recovery.get("resume_plans")):
        add(
            source_ref=item.get("plan_ref") or "recovery:resume_plan",
            title=item.get("title") or "续接恢复计划",
            action_hint=item.get("next_action") or "按 ResumePlan 续接长链任务。",
            action_type="resume_plan",
            risk_level="A2",
            priority="P0_resume",
        )
    for item in _as_dicts(governance.get("planner_hints")):
        add(
            source_ref=item.get("hint_ref") or item.get("source_ref") or "governance:planner_hint",
            title=item.get("title") or "治理执行提示",
            action_hint=item.get("next_action") or "按治理提示执行快车道草案，遇到硬边界停止。",
            action_type="governance_hint",
            risk_level="A2",
            priority="P0_governance",
            stop_condition=item.get("stop_condition") or "触发 A5 或正式发布/注册/激活。",
        )
    for item in _as_dicts(repair.get("patch_plan")):
        add(
            source_ref=item.get("step_id") or "project_repair:patch_plan",
            title=f"工程修复草案：{item.get('operation', 'patch_plan')}",
            action_hint=item.get("rationale") or "按 PatchPlan 生成最小补丁草案并复测。",
            action_type="patch_plan",
            risk_level=_normalize_risk(item.get("risk_level") or "A2"),
            priority="P1_repair",
            requires_confirmation=_normalize_risk(item.get("risk_level") or "A2") == "A4",
        )
    for item in _as_dicts(provider.get("api_surface_routes"))[:3]:
        add(
            source_ref=item.get("surface_id") or item.get("provider_id") or "provider:surface",
            title=f"Provider 声明式候选：{item.get('provider_id', 'provider')}",
            action_hint="只把 Provider 能力矩阵作为 Planner 约束；真实模型调用必须经 L4/L5 Runtime 治理链。",
            action_type="provider_surface_option",
            risk_level="A4",
            priority="P1_provider",
            fast_lane=False,
            requires_confirmation=True,
            stop_condition="出现明文凭证、裸 SDK、L6 直连网络或未授权 Provider 调用。",
        )
    if delivery.get("schema") and len(hints) < limit:
        add(
            source_ref="delivery_standardization:requirements",
            title="交付证据链收口",
            action_hint="正式交付前整理修改清单、测试证据、manifest、integrity 和未做事项；质量门只卡发布。",
            action_type="delivery_requirements",
            risk_level="A2",
            priority="P1_delivery",
        )
    if shell.get("schema") and len(hints) < limit:
        add(
            source_ref="shell_mount:18_systems",
            title="18 系统挂载图消费",
            action_hint="把 active/partial 系统槽作为 Planner 可见能力地图，不注册正式工具或 Skill。",
            action_type="shell_system_mount",
            risk_level="A2",
            priority="P1_shell",
        )
    for item in boundaries:
        if len(hints) >= limit:
            break
        if item.get("risk_level") == "A5":
            add(
                source_ref=item.get("boundary_ref") or item.get("source_ref") or "boundary:a5",
                title=item.get("boundary_name") or "A5 硬边界",
                action_hint=item.get("action") or "阻断并重新规划。",
                action_type="hard_boundary",
                risk_level="A5",
                priority="P0_boundary",
                fast_lane=False,
                requires_confirmation=True,
                blocks_execution=True,
                stop_condition=item.get("trigger") or "A5 硬边界。",
            )
    if not hints:
        add(
            source_ref="planner_context:default",
            title="默认统一 Planner 上下文",
            action_hint="先补 ShellMount / Repair / Delivery / Learning / Recovery / Governance，再生成具体执行草案。",
            action_type="default_unified_context",
            risk_level="A2",
        )
    return hints[:limit]



def _execution_steps(
    hints: list[UnifiedPlannerHint],
    regression_targets: list[dict[str, Any]],
    delivery_requirements: list[dict[str, Any]],
    *,
    limit: int,
) -> list[ExecutionStepDraft]:
    steps: list[ExecutionStepDraft] = []
    for hint in hints:
        if len(steps) >= limit:
            break
        if hint.blocks_execution:
            # 硬边界作为 blocked_actions，不进入下一步执行草案。
            continue
        suggested = _suggested_tool_for_hint(hint)
        evidence = _expected_evidence_for_hint(hint, regression_targets, delivery_requirements)
        steps.append(
            ExecutionStepDraft(
                step_id=_ref("step", hint.hint_ref, len(steps)),
                title=hint.title,
                source_hint=hint.hint_ref,
                action_type=hint.action_type,
                risk_level=hint.risk_level,
                requires_confirmation=hint.requires_confirmation,
                suggested_tool_or_shell=suggested,
                expected_evidence=evidence,
                fallback_or_rollback="失败时回退到 RecoveryResumeEnvelope；涉及写入/发布/注册/激活时先要求备份、hash compare 和质量门。",
                fast_lane_candidate=hint.fast_lane_candidate and not hint.requires_confirmation,
            )
        )
    if not steps:
        steps.append(
            ExecutionStepDraft(
                step_id="step:default_read_context",
                title="读取统一 Planner 上下文",
                source_hint="planner_context:default",
                action_type="read_unified_context",
                risk_level="A1",
                requires_confirmation=False,
                suggested_tool_or_shell="planner_context_integration",
                expected_evidence="PlannerContextReport.public_dict() 可序列化并包含下一步上下文。",
                fallback_or_rollback="缺少源报告时 graceful degradation，继续补建 L6.24-L6.30 前置信息。",
            )
        )
    return steps[:limit]



def _suggested_tool_for_hint(hint: UnifiedPlannerHint) -> str:
    mapping = {
        "learning_consumption_card": "build_learning_convergence / planner_context",
        "resume_plan": "build_recovery_coordination / planner_context",
        "governance_hint": "build_governance_execution / planner_context",
        "patch_plan": "build_project_repair_plan / run_python_quality_check(smoke only after confirmation if writing)",
        "provider_surface_option": "build_provider_adaptation / L4-L5 governed provider route",
        "delivery_requirements": "build_delivery_standardization",
        "shell_system_mount": "build_shell_system_mount",
    }
    return mapping.get(hint.action_type, "planner_context")



def _expected_evidence_for_hint(
    hint: UnifiedPlannerHint,
    regression_targets: list[dict[str, Any]],
    delivery_requirements: list[dict[str, Any]],
) -> str:
    if hint.action_type == "patch_plan" and regression_targets:
        first = regression_targets[0]
        return f"RegressionHint: {first.get('command', 'pytest')} {first.get('target', '.')} 的结果摘要。"
    if hint.action_type == "delivery_requirements" and delivery_requirements:
        return "DeliveryStandardizationReport: ChangeSet/TestEvidence/Manifest/Integrity/Todo 全量摘要。"
    if hint.action_type == "provider_surface_option":
        return "ProviderAdaptationReport: API Surface 仅声明式候选，无 live_call_enabled。"
    if hint.action_type == "resume_plan":
        return "RecoveryCoordinationReport: ResumePlan / BudgetUpdate / HandoffDigest 摘要。"
    return "PlannerContextReport: 统一上下文、风险边界、下一步草案均可 JSON 序列化。"



def _summary(
    *,
    sources: list[PlannerSourceEvidence],
    hints: list[UnifiedPlannerHint],
    steps: list[ExecutionStepDraft],
    fast_lane_actions: list[dict[str, Any]],
    blocked_actions: list[dict[str, Any]],
    confirmations: list[dict[str, Any]],
    notes: str,
) -> str:
    active_sources = sum(1 for item in sources if item.status not in {"empty", "unknown"})
    fast_hints = sum(1 for item in hints if item.fast_lane_candidate)
    blocked_hints = sum(1 for item in hints if item.blocks_execution)
    summary = (
        f"已把 L6.24-L6.30 外壳输出压缩为单一 UnifiedPlannerContext：source={len(sources)}，"
        f"active_source={active_sources}，planner_hint={len(hints)}，fast_hint={fast_hints}，blocked_hint={blocked_hints}，"
        f"execution_step_draft={len(steps)}，fast_lane_action={len(fast_lane_actions)}，blocked_action={len(blocked_actions)}，"
        f"required_confirmation={len(confirmations)}。A0-A4 草案/分析/smoke/续接进入快车道；"
        "A5、凭证、内核、Provider 裸调、正式发布/注册/激活仍保持硬边界。"
    )
    if notes:
        summary += f" 用户备注：{notes}"
    return summary



def _source_schemas(*reports: dict[str, Any]) -> list[str]:
    schemas: list[str] = []
    for report in reports:
        if isinstance(report, dict):
            schema = _safe_text(report.get("schema"), limit=180)
            if schema and schema not in schemas:
                schemas.append(schema)
    return schemas



def _normalize_risk(value: Any) -> str:
    text = _safe_text(value, limit=60).upper()
    for level in ("A5", "A4", "A3", "A2", "A1", "A0"):
        if level in text:
            return level
    return "A2"



def _safe_dict_list(value: Any, *, limit: int) -> list[dict[str, Any]]:
    return [_safe_payload(item) for item in _as_dicts(value)[:limit]]



def _safe_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _safe_payload(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_safe_payload(item) for item in value]
    if isinstance(value, tuple):
        return [_safe_payload(item) for item in value]
    if isinstance(value, (bool, int, float)) or value is None:
        return value
    return _safe_text(value, limit=700)



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
