"""L6.42 SelfHealing 接入路由。

本模块把失败、质量门、恢复票据和回放证据压缩成 Planner 可消费的
自愈候选。它只提出诊断、恢复、验证与回归建议，不自动修代码、不执行补丁、
不回滚、不热切换、不调工具、不污染核心组。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any
import hashlib
import json

from tiangong_kernel.l6_plugins.common._common import ensure_bool, ensure_score

L6_42_SELF_HEALING_SCHEMA = "tiangong.l6_42.self_healing_execution_route.v1"


def _digest(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _text(value: Any, limit: int = 360) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\x00", "").replace("\r", " ").replace("\n", " ").strip()
    lowered = text.lower()
    for marker in ("api_key", "apikey", "authorization", "bearer ", "token", "secret", "password", "credential"):
        if marker in lowered:
            return "[redacted-sensitive-summary]"
    return text[:limit]


def _score(value: float, field_name: str) -> None:
    ensure_score(value, field_name)


def _non_negative_int(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be non-negative int")


@dataclass(frozen=True)
class SelfHealingSignal:
    """自愈信号摘要，只保留安全分类与引用。"""

    signal_ref: str
    failure_type: str = "unknown"
    severity: str = "P2"
    source_ref: str = "report:l6_42_failure_source"
    evidence_refs: list[str] = field(default_factory=list)
    confidence_score: float = 0.70

    def __post_init__(self) -> None:
        for field_name in ("signal_ref", "failure_type", "severity", "source_ref"):
            if not _text(getattr(self, field_name), 240):
                raise ValueError(f"SelfHealingSignal.{field_name} must be non-empty text")
        _score(self.confidence_score, "SelfHealingSignal.confidence_score")

    def public_dict(self) -> dict[str, Any]:
        return {
            "signal_ref": _text(self.signal_ref, 240),
            "failure_type": _text(self.failure_type, 120),
            "severity": _text(self.severity, 40),
            "source_ref": _text(self.source_ref, 240),
            "evidence_refs": [_text(item, 240) for item in self.evidence_refs],
            "confidence_score": self.confidence_score,
        }


@dataclass(frozen=True)
class SelfHealingExecutionRoute:
    """Planner 可消费的自愈接入路由。"""

    route_id: str
    generated_at: float = field(default_factory=time)
    healing_need_score: float = 0.0
    failure_signals: list[SelfHealingSignal] = field(default_factory=list)
    recovery_ticket_refs: list[str] = field(default_factory=list)
    validation_need_refs: list[str] = field(default_factory=list)
    regression_need_refs: list[str] = field(default_factory=list)
    planner_hint: str = ""
    priority: str = "P1_current_task_failure_recovery"
    planner_consumable: bool = True
    candidate_only: bool = True
    requires_planner_step: bool = True
    no_direct_execution: bool = True
    no_tool_invocation: bool = True
    no_patch_execution: bool = True
    no_file_write: bool = True
    no_rollback: bool = True
    no_hot_switch: bool = True
    no_kernel_mutation: bool = True
    invokes_tool: bool = False
    applies_patch: bool = False
    writes_file: bool = False
    performs_rollback: bool = False
    performs_hot_switch: bool = False
    mutates_kernel: bool = False

    def __post_init__(self) -> None:
        if not _text(self.route_id, 240):
            raise ValueError("SelfHealingExecutionRoute.route_id must be non-empty text")
        _score(self.healing_need_score, "SelfHealingExecutionRoute.healing_need_score")
        for field_name in (
            "planner_consumable",
            "candidate_only",
            "requires_planner_step",
            "no_direct_execution",
            "no_tool_invocation",
            "no_patch_execution",
            "no_file_write",
            "no_rollback",
            "no_hot_switch",
            "no_kernel_mutation",
            "invokes_tool",
            "applies_patch",
            "writes_file",
            "performs_rollback",
            "performs_hot_switch",
            "mutates_kernel",
        ):
            ensure_bool(getattr(self, field_name), f"SelfHealingExecutionRoute.{field_name}")
        required = (
            self.planner_consumable,
            self.candidate_only,
            self.requires_planner_step,
            self.no_direct_execution,
            self.no_tool_invocation,
            self.no_patch_execution,
            self.no_file_write,
            self.no_rollback,
            self.no_hot_switch,
            self.no_kernel_mutation,
        )
        if not all(required):
            raise ValueError("SelfHealingExecutionRoute must remain candidate-only and planner-routed")
        forbidden = (
            self.invokes_tool,
            self.applies_patch,
            self.writes_file,
            self.performs_rollback,
            self.performs_hot_switch,
            self.mutates_kernel,
        )
        if any(forbidden):
            raise ValueError("SelfHealingExecutionRoute cannot execute healing side effects")

    @property
    def signal_count(self) -> int:
        return len(self.failure_signals)

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_42_SELF_HEALING_SCHEMA,
            "route_id": _text(self.route_id, 240),
            "generated_at": self.generated_at,
            "healing_need_score": self.healing_need_score,
            "failure_signals": [item.public_dict() for item in self.failure_signals],
            "recovery_ticket_refs": [_text(item, 240) for item in self.recovery_ticket_refs],
            "validation_need_refs": [_text(item, 240) for item in self.validation_need_refs],
            "regression_need_refs": [_text(item, 240) for item in self.regression_need_refs],
            "planner_hint": _text(self.planner_hint, 900),
            "priority": self.priority,
            "planner_consumable": self.planner_consumable,
            "candidate_only": self.candidate_only,
            "requires_planner_step": self.requires_planner_step,
            "no_direct_execution": self.no_direct_execution,
            "no_tool_invocation": self.no_tool_invocation,
            "no_patch_execution": self.no_patch_execution,
            "no_file_write": self.no_file_write,
            "no_rollback": self.no_rollback,
            "no_hot_switch": self.no_hot_switch,
            "no_kernel_mutation": self.no_kernel_mutation,
            "invokes_tool": self.invokes_tool,
            "applies_patch": self.applies_patch,
            "writes_file": self.writes_file,
            "performs_rollback": self.performs_rollback,
            "performs_hot_switch": self.performs_hot_switch,
            "mutates_kernel": self.mutates_kernel,
        }


def build_self_healing_route(
    *,
    planner_report: Any | None = None,
    recovery_ticket: Any | None = None,
    quality_gate: Any | None = None,
    replay_quality: Any | None = None,
    notes: str = "",
) -> SelfHealingExecutionRoute:
    """从执行报告和恢复证据生成自愈候选路由。"""

    signals: list[SelfHealingSignal] = []
    failed = int(getattr(planner_report, "failed_steps", 0) or 0) if planner_report is not None else 0
    timeout = int(getattr(planner_report, "timeout_steps", 0) or 0) if planner_report is not None else 0
    blocked = int(getattr(planner_report, "blocked_steps", 0) or 0) if planner_report is not None else 0
    confirmation = int(getattr(planner_report, "confirmation_required_steps", 0) or 0) if planner_report is not None else 0
    for name, count, severity in (
        ("failed_steps", failed, "P1"),
        ("timeout_steps", timeout, "P1"),
        ("blocked_steps", blocked, "P0"),
        ("confirmation_required_steps", confirmation, "P2"),
    ):
        _non_negative_int(count, name)
        if count:
            signals.append(
                SelfHealingSignal(
                    signal_ref=f"healing:l6_42_{name}_{count}",
                    failure_type=name,
                    severity=severity,
                    source_ref=_text(getattr(planner_report, "task_id", "report:l6_42_planner_report"), 180) or "report:l6_42_planner_report",
                    evidence_refs=[_text(getattr(planner_report, "run_id", "run:l6_42"), 180) or "run:l6_42"],
                    confidence_score=0.82,
                )
            )
    gate_decision = _text(getattr(quality_gate, "decision", ""), 80) if quality_gate is not None else ""
    if gate_decision and gate_decision not in {"pass", "warn", "not_evaluated"}:
        signals.append(
            SelfHealingSignal(
                signal_ref=f"healing:l6_42_quality_gate_{_digest(gate_decision)}",
                failure_type="quality_gate_issue",
                severity="P1",
                source_ref=_text(getattr(quality_gate, "evidence_id", "quality:l6_42_gate"), 180) or "quality:l6_42_gate",
                evidence_refs=[_text(gate_decision, 120)],
                confidence_score=0.76,
            )
        )
    unresolved = getattr(replay_quality, "unresolved_failures", None)
    if isinstance(unresolved, list) and unresolved:
        signals.append(
            SelfHealingSignal(
                signal_ref=f"healing:l6_42_replay_unresolved_{len(unresolved)}",
                failure_type="replay_unresolved_failure",
                severity="P1",
                source_ref="report:l6_42_replay_quality",
                evidence_refs=[_text(item, 120) for item in unresolved[:5]],
                confidence_score=0.78,
            )
        )
    ticket_ref = _text(getattr(recovery_ticket, "ticket_id", ""), 180) if recovery_ticket is not None else ""
    recovery_refs = [ticket_ref] if ticket_ref else []
    need = min(1.0, 0.18 * len(signals) + 0.10 * bool(recovery_refs) + 0.08 * bool(_text(notes, 80)))
    hint = "SelfHealing 接入：发现失败/质量/回放信号时，只生成诊断、恢复、验证与回归建议；真实修复必须变成 Planner Step 后进入 ExecutionSpine。"
    if signals:
        hint += f" 本轮自愈候选信号 {len(signals)} 个，优先做最小恢复与复测。"
    elif notes:
        hint += f" 备注：{_text(notes, 180)}"
    return SelfHealingExecutionRoute(
        route_id=f"healing_route:{_digest([item.public_dict() for item in signals] + recovery_refs + [notes])}",
        healing_need_score=need,
        failure_signals=signals,
        recovery_ticket_refs=recovery_refs,
        validation_need_refs=["validation:l6_42_self_healing_required"] if signals else [],
        regression_need_refs=["regression:l6_42_self_healing_required"] if signals else [],
        planner_hint=hint,
    )
