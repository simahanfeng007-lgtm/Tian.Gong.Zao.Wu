"""L6.45 回滚审计全链绑定。

本模块把 PlannerExecutionReport 的安全公开摘要绑定为四类可回放证据：
- StateDeltaLedger：每步状态变化账本；
- ToolDependencyGraph：工具步骤依赖图；
- RecoveryCheckpoint：断点续接与回滚检查点；
- AuditEvidenceEnvelope：审计证据封包。

它只做 runtime 外壳层的 ref / digest / summary 绑定，不调工具、不执行回滚、
不写内核、不修改预算、不注册 Tool/Skill。真实执行仍必须回到 L6.37 执行链。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import Any, Iterable

from tiangong_kernel.l6_plugins.common._common import ensure_bool

from .four_path_public_projection import sanitize_text, stable_digest

L6_45_ROLLBACK_AUDIT_SCHEMA = "tiangong.l6_45.rollback_audit_binding.v1"
SOURCE_VERSION = "L6.45-rollback-audit-binding"

IRREVERSIBLE_TERMS = (
    "delete",
    "remove",
    "purge",
    "drop",
    "destroy",
    "publish",
    "release",
    "deploy",
    "activate",
    "register",
    "merge",
    "hot_switch",
    "version_slot",
    "credential",
    "secret",
)
TERMINAL_STATES = {
    "succeeded",
    "failed",
    "blocked",
    "confirmation_required",
    "skipped",
    "recovered",
    "timeout",
}


def _payload_of(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    public = getattr(value, "public_dict", None)
    if callable(public):
        result = public()
        if isinstance(result, dict):
            return dict(result)
    return {"summary": sanitize_text(value)}


def _as_tuple(values: Iterable[Any] | None, *, limit: int = 50) -> tuple[Any, ...]:
    if values is None:
        return tuple()
    return tuple(list(values)[: max(0, int(limit))])


def _safe_ref(prefix: str, *parts: Any, limit: int = 180) -> str:
    joined = ":".join(sanitize_text(part, limit=80) for part in parts if sanitize_text(part, limit=80))
    return sanitize_text(f"{prefix}:{joined}" if joined else prefix, limit=limit)


def _step_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records = payload.get("step_records") or []
    if not isinstance(records, list):
        return []
    return [dict(item) for item in records if isinstance(item, dict)]


def _report_digest(payload: dict[str, Any]) -> str:
    explicit = sanitize_text(payload.get("report_digest"), limit=80)
    return explicit or stable_digest(payload, length=24)


def _is_irreversible(tool_name: str, reason: str = "", summary: str = "") -> bool:
    text = f"{tool_name} {reason} {summary}".lower()
    return any(term in text for term in IRREVERSIBLE_TERMS)


@dataclass(frozen=True)
class StateDeltaRecord:
    """单步状态变化记录。只描述变化，不执行回滚。"""

    delta_id: str
    step_id: str
    tool_name: str
    state: str
    audit_ref: str = ""
    before_ref: str = ""
    after_ref: str = ""
    argument_digest: str = ""
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    artifact_refs: tuple[str, ...] = field(default_factory=tuple)
    changes_summary: str = ""
    reversible: bool = True
    rollback_strategy: str = "restore_checkpoint"
    rollback_hint: str = ""
    risk_level: str = ""
    error_code: str = ""
    source_digest: str = ""
    no_raw_body: bool = True
    no_secret_read: bool = True
    no_direct_execution: bool = True
    no_rollback_execution: bool = True
    no_budget_mutation: bool = True
    no_registry_mutation: bool = True
    no_kernel_mutation: bool = True

    def __post_init__(self) -> None:
        for name in (
            "reversible",
            "no_raw_body",
            "no_secret_read",
            "no_direct_execution",
            "no_rollback_execution",
            "no_budget_mutation",
            "no_registry_mutation",
            "no_kernel_mutation",
        ):
            ensure_bool(getattr(self, name), f"StateDeltaRecord.{name}")
        if self.state not in TERMINAL_STATES:
            raise ValueError("StateDeltaRecord.state must be terminal")
        if not sanitize_text(self.delta_id, limit=240) or not sanitize_text(self.step_id, limit=160):
            raise ValueError("StateDeltaRecord requires delta_id and step_id")
        if not all(
            (
                self.no_raw_body,
                self.no_secret_read,
                self.no_direct_execution,
                self.no_rollback_execution,
                self.no_budget_mutation,
                self.no_registry_mutation,
                self.no_kernel_mutation,
            )
        ):
            raise ValueError("StateDeltaRecord must remain projection-only")

    @property
    def delta_digest(self) -> str:
        return stable_digest(
            {
                "delta_id": self.delta_id,
                "step_id": self.step_id,
                "tool_name": self.tool_name,
                "state": self.state,
                "audit_ref": self.audit_ref,
                "before_ref": self.before_ref,
                "after_ref": self.after_ref,
                "argument_digest": self.argument_digest,
                "evidence_refs": list(self.evidence_refs),
                "artifact_refs": list(self.artifact_refs),
                "reversible": self.reversible,
                "rollback_strategy": self.rollback_strategy,
            },
            length=24,
        )

    def public_dict(self) -> dict[str, Any]:
        return {
            "delta_id": sanitize_text(self.delta_id, limit=240),
            "step_id": sanitize_text(self.step_id, limit=160),
            "tool_name": sanitize_text(self.tool_name, limit=160),
            "state": sanitize_text(self.state, limit=80),
            "audit_ref": sanitize_text(self.audit_ref, limit=160),
            "before_ref": sanitize_text(self.before_ref, limit=200),
            "after_ref": sanitize_text(self.after_ref, limit=200),
            "argument_digest": sanitize_text(self.argument_digest, limit=80),
            "evidence_refs": [sanitize_text(item, limit=200) for item in self.evidence_refs],
            "artifact_refs": [sanitize_text(item, limit=200) for item in self.artifact_refs],
            "changes_summary": sanitize_text(self.changes_summary, limit=420),
            "reversible": self.reversible,
            "rollback_strategy": sanitize_text(self.rollback_strategy, limit=120),
            "rollback_hint": sanitize_text(self.rollback_hint, limit=420),
            "risk_level": sanitize_text(self.risk_level, limit=80),
            "error_code": sanitize_text(self.error_code, limit=120),
            "source_digest": sanitize_text(self.source_digest, limit=80),
            "delta_digest": self.delta_digest,
            "no_raw_body": self.no_raw_body,
            "no_secret_read": self.no_secret_read,
            "no_direct_execution": self.no_direct_execution,
            "no_rollback_execution": self.no_rollback_execution,
            "no_budget_mutation": self.no_budget_mutation,
            "no_registry_mutation": self.no_registry_mutation,
            "no_kernel_mutation": self.no_kernel_mutation,
        }


@dataclass(frozen=True)
class StateDeltaLedger:
    """状态变化账本。账本是 append-only 公开摘要，不修改真实状态。"""

    ledger_id: str
    source_report_digest: str
    deltas: tuple[StateDeltaRecord, ...] = field(default_factory=tuple)
    generated_at: float = field(default_factory=time)
    append_only: bool = True
    projection_only: bool = True
    replayable: bool = True
    no_raw_body: bool = True
    no_direct_execution: bool = True
    no_rollback_execution: bool = True
    no_budget_mutation: bool = True
    no_registry_mutation: bool = True
    no_kernel_mutation: bool = True

    def __post_init__(self) -> None:
        for name in (
            "append_only",
            "projection_only",
            "replayable",
            "no_raw_body",
            "no_direct_execution",
            "no_rollback_execution",
            "no_budget_mutation",
            "no_registry_mutation",
            "no_kernel_mutation",
        ):
            ensure_bool(getattr(self, name), f"StateDeltaLedger.{name}")
        if not all(
            (
                self.append_only,
                self.projection_only,
                self.replayable,
                self.no_raw_body,
                self.no_direct_execution,
                self.no_rollback_execution,
                self.no_budget_mutation,
                self.no_registry_mutation,
                self.no_kernel_mutation,
            )
        ):
            raise ValueError("StateDeltaLedger must remain append-only projection")

    @property
    def ledger_digest(self) -> str:
        return stable_digest([delta.public_dict() for delta in self.deltas], length=24)

    @property
    def reversible_delta_count(self) -> int:
        return sum(1 for delta in self.deltas if delta.reversible)

    @property
    def manual_review_delta_count(self) -> int:
        return sum(1 for delta in self.deltas if not delta.reversible)

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_45_ROLLBACK_AUDIT_SCHEMA,
            "source_version": SOURCE_VERSION,
            "ledger_id": sanitize_text(self.ledger_id, limit=240),
            "source_report_digest": sanitize_text(self.source_report_digest, limit=80),
            "generated_at": self.generated_at,
            "delta_count": len(self.deltas),
            "reversible_delta_count": self.reversible_delta_count,
            "manual_review_delta_count": self.manual_review_delta_count,
            "deltas": [delta.public_dict() for delta in self.deltas],
            "ledger_digest": self.ledger_digest,
            "append_only": self.append_only,
            "projection_only": self.projection_only,
            "replayable": self.replayable,
            "no_raw_body": self.no_raw_body,
            "no_direct_execution": self.no_direct_execution,
            "no_rollback_execution": self.no_rollback_execution,
            "no_budget_mutation": self.no_budget_mutation,
            "no_registry_mutation": self.no_registry_mutation,
            "no_kernel_mutation": self.no_kernel_mutation,
        }

    def export_jsonl(self, path: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as fh:
            for delta in self.deltas:
                fh.write(json.dumps(delta.public_dict(), ensure_ascii=False, sort_keys=True) + "\n")
        return target


@dataclass(frozen=True)
class ToolDependencyNode:
    node_id: str
    step_id: str
    tool_name: str
    state: str = "planned"
    audit_ref: str = ""
    delta_ref: str = ""

    def public_dict(self) -> dict[str, Any]:
        return {
            "node_id": sanitize_text(self.node_id, limit=200),
            "step_id": sanitize_text(self.step_id, limit=160),
            "tool_name": sanitize_text(self.tool_name, limit=160),
            "state": sanitize_text(self.state, limit=80),
            "audit_ref": sanitize_text(self.audit_ref, limit=160),
            "delta_ref": sanitize_text(self.delta_ref, limit=200),
        }


@dataclass(frozen=True)
class ToolDependencyEdge:
    edge_id: str
    from_step_id: str
    to_step_id: str
    relation: str = "depends_on"
    required: bool = True

    def __post_init__(self) -> None:
        ensure_bool(self.required, "ToolDependencyEdge.required")
        if not self.from_step_id or not self.to_step_id:
            raise ValueError("ToolDependencyEdge requires from_step_id and to_step_id")

    def public_dict(self) -> dict[str, Any]:
        return {
            "edge_id": sanitize_text(self.edge_id, limit=200),
            "from_step_id": sanitize_text(self.from_step_id, limit=160),
            "to_step_id": sanitize_text(self.to_step_id, limit=160),
            "relation": sanitize_text(self.relation, limit=80),
            "required": self.required,
        }


@dataclass(frozen=True)
class ToolDependencyGraph:
    """工具依赖图。只做依赖投影，不执行调度。"""

    graph_id: str
    source_report_digest: str
    nodes: tuple[ToolDependencyNode, ...] = field(default_factory=tuple)
    edges: tuple[ToolDependencyEdge, ...] = field(default_factory=tuple)
    missing_dependency_refs: tuple[str, ...] = field(default_factory=tuple)
    failed_step_ids: tuple[str, ...] = field(default_factory=tuple)
    blocked_step_ids: tuple[str, ...] = field(default_factory=tuple)
    projection_only: bool = True
    no_direct_execution: bool = True
    no_tool_dispatch: bool = True
    no_scheduler_override: bool = True
    no_kernel_mutation: bool = True

    def __post_init__(self) -> None:
        for name in (
            "projection_only",
            "no_direct_execution",
            "no_tool_dispatch",
            "no_scheduler_override",
            "no_kernel_mutation",
        ):
            ensure_bool(getattr(self, name), f"ToolDependencyGraph.{name}")
        if not all((self.projection_only, self.no_direct_execution, self.no_tool_dispatch, self.no_scheduler_override, self.no_kernel_mutation)):
            raise ValueError("ToolDependencyGraph must remain projection-only")

    @property
    def graph_digest(self) -> str:
        return stable_digest(
            {
                "nodes": [node.public_dict() for node in self.nodes],
                "edges": [edge.public_dict() for edge in self.edges],
                "missing": list(self.missing_dependency_refs),
                "failed": list(self.failed_step_ids),
                "blocked": list(self.blocked_step_ids),
            },
            length=24,
        )

    def impacted_steps_from_failed(self) -> tuple[str, ...]:
        failed = set(self.failed_step_ids) | set(self.blocked_step_ids)
        impacted: set[str] = set()
        changed = True
        while changed:
            changed = False
            for edge in self.edges:
                if edge.from_step_id in failed or edge.from_step_id in impacted:
                    if edge.to_step_id not in impacted:
                        impacted.add(edge.to_step_id)
                        changed = True
        return tuple(sorted(impacted))

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_45_ROLLBACK_AUDIT_SCHEMA,
            "source_version": SOURCE_VERSION,
            "graph_id": sanitize_text(self.graph_id, limit=240),
            "source_report_digest": sanitize_text(self.source_report_digest, limit=80),
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "nodes": [node.public_dict() for node in self.nodes],
            "edges": [edge.public_dict() for edge in self.edges],
            "missing_dependency_refs": [sanitize_text(item, limit=200) for item in self.missing_dependency_refs],
            "failed_step_ids": [sanitize_text(item, limit=160) for item in self.failed_step_ids],
            "blocked_step_ids": [sanitize_text(item, limit=160) for item in self.blocked_step_ids],
            "impacted_steps": list(self.impacted_steps_from_failed()),
            "graph_digest": self.graph_digest,
            "projection_only": self.projection_only,
            "no_direct_execution": self.no_direct_execution,
            "no_tool_dispatch": self.no_tool_dispatch,
            "no_scheduler_override": self.no_scheduler_override,
            "no_kernel_mutation": self.no_kernel_mutation,
        }


@dataclass(frozen=True)
class RecoveryCheckpoint:
    """恢复检查点。只描述可续接与回滚要求，不执行恢复。"""

    checkpoint_id: str
    source_report_digest: str
    last_completed_step_id: str = ""
    next_step_id: str = ""
    resume_mode: str = "resume_from_next_step"
    can_resume: bool = True
    rollback_required: bool = False
    rollback_plan_ref: str = ""
    validation_required: bool = True
    state_delta_refs: tuple[str, ...] = field(default_factory=tuple)
    audit_refs: tuple[str, ...] = field(default_factory=tuple)
    dependency_graph_ref: str = ""
    checkpoint_digest: str = ""
    no_direct_execution: bool = True
    no_rollback_execution: bool = True
    no_hot_switch: bool = True
    no_quality_gate_override: bool = True
    no_kernel_mutation: bool = True

    def __post_init__(self) -> None:
        for name in (
            "can_resume",
            "rollback_required",
            "validation_required",
            "no_direct_execution",
            "no_rollback_execution",
            "no_hot_switch",
            "no_quality_gate_override",
            "no_kernel_mutation",
        ):
            ensure_bool(getattr(self, name), f"RecoveryCheckpoint.{name}")
        if not all((self.no_direct_execution, self.no_rollback_execution, self.no_hot_switch, self.no_quality_gate_override, self.no_kernel_mutation)):
            raise ValueError("RecoveryCheckpoint cannot execute rollback or override gates")

    def public_dict(self) -> dict[str, Any]:
        digest = self.checkpoint_digest or stable_digest(
            {
                "checkpoint_id": self.checkpoint_id,
                "source_report_digest": self.source_report_digest,
                "last_completed_step_id": self.last_completed_step_id,
                "next_step_id": self.next_step_id,
                "resume_mode": self.resume_mode,
                "state_delta_refs": list(self.state_delta_refs),
                "audit_refs": list(self.audit_refs),
                "dependency_graph_ref": self.dependency_graph_ref,
            },
            length=24,
        )
        return {
            "schema": L6_45_ROLLBACK_AUDIT_SCHEMA,
            "source_version": SOURCE_VERSION,
            "checkpoint_id": sanitize_text(self.checkpoint_id, limit=240),
            "source_report_digest": sanitize_text(self.source_report_digest, limit=80),
            "last_completed_step_id": sanitize_text(self.last_completed_step_id, limit=160),
            "next_step_id": sanitize_text(self.next_step_id, limit=160),
            "resume_mode": sanitize_text(self.resume_mode, limit=120),
            "can_resume": self.can_resume,
            "rollback_required": self.rollback_required,
            "rollback_plan_ref": sanitize_text(self.rollback_plan_ref, limit=220),
            "validation_required": self.validation_required,
            "state_delta_refs": [sanitize_text(item, limit=220) for item in self.state_delta_refs],
            "audit_refs": [sanitize_text(item, limit=160) for item in self.audit_refs],
            "dependency_graph_ref": sanitize_text(self.dependency_graph_ref, limit=220),
            "checkpoint_digest": digest,
            "no_direct_execution": self.no_direct_execution,
            "no_rollback_execution": self.no_rollback_execution,
            "no_hot_switch": self.no_hot_switch,
            "no_quality_gate_override": self.no_quality_gate_override,
            "no_kernel_mutation": self.no_kernel_mutation,
        }


@dataclass(frozen=True)
class AuditEvidenceEnvelope:
    """审计证据封包。证据只给 ref/digest，不暴露完整正文。"""

    envelope_id: str
    source_report_digest: str
    audit_refs: tuple[str, ...] = field(default_factory=tuple)
    state_delta_refs: tuple[str, ...] = field(default_factory=tuple)
    dependency_graph_ref: str = ""
    recovery_checkpoint_ref: str = ""
    evidence_digest: str = ""
    summary: str = ""
    evidence_ref_only: bool = True
    no_full_evidence_body: bool = True
    no_raw_prompt: bool = True
    no_plain_secret: bool = True
    no_direct_execution: bool = True
    no_rollback_execution: bool = True
    no_kernel_mutation: bool = True

    def __post_init__(self) -> None:
        for name in (
            "evidence_ref_only",
            "no_full_evidence_body",
            "no_raw_prompt",
            "no_plain_secret",
            "no_direct_execution",
            "no_rollback_execution",
            "no_kernel_mutation",
        ):
            ensure_bool(getattr(self, name), f"AuditEvidenceEnvelope.{name}")
        if not all(
            (
                self.evidence_ref_only,
                self.no_full_evidence_body,
                self.no_raw_prompt,
                self.no_plain_secret,
                self.no_direct_execution,
                self.no_rollback_execution,
                self.no_kernel_mutation,
            )
        ):
            raise ValueError("AuditEvidenceEnvelope must remain ref-only")

    def public_dict(self) -> dict[str, Any]:
        digest = self.evidence_digest or stable_digest(
            {
                "audit_refs": list(self.audit_refs),
                "state_delta_refs": list(self.state_delta_refs),
                "dependency_graph_ref": self.dependency_graph_ref,
                "recovery_checkpoint_ref": self.recovery_checkpoint_ref,
                "summary": self.summary,
            },
            length=24,
        )
        return {
            "schema": L6_45_ROLLBACK_AUDIT_SCHEMA,
            "source_version": SOURCE_VERSION,
            "envelope_id": sanitize_text(self.envelope_id, limit=240),
            "source_report_digest": sanitize_text(self.source_report_digest, limit=80),
            "audit_refs": [sanitize_text(item, limit=160) for item in self.audit_refs],
            "state_delta_refs": [sanitize_text(item, limit=220) for item in self.state_delta_refs],
            "dependency_graph_ref": sanitize_text(self.dependency_graph_ref, limit=220),
            "recovery_checkpoint_ref": sanitize_text(self.recovery_checkpoint_ref, limit=220),
            "evidence_digest": digest,
            "summary": sanitize_text(self.summary, limit=600),
            "evidence_ref_only": self.evidence_ref_only,
            "no_full_evidence_body": self.no_full_evidence_body,
            "no_raw_prompt": self.no_raw_prompt,
            "no_plain_secret": self.no_plain_secret,
            "no_direct_execution": self.no_direct_execution,
            "no_rollback_execution": self.no_rollback_execution,
            "no_kernel_mutation": self.no_kernel_mutation,
        }


@dataclass(frozen=True)
class RollbackAuditBindingReport:
    report_id: str
    status: str
    state_delta_ledger: StateDeltaLedger
    dependency_graph: ToolDependencyGraph
    recovery_checkpoint: RecoveryCheckpoint
    audit_evidence_envelope: AuditEvidenceEnvelope
    issues: tuple[str, ...] = field(default_factory=tuple)
    generated_at: float = field(default_factory=time)
    planner_consumable: bool = True
    replayable: bool = True
    rollback_audit_bound: bool = True
    no_second_runtime: bool = True
    no_direct_execution: bool = True
    no_rollback_execution: bool = True
    no_tool_dispatch: bool = True
    no_budget_mutation: bool = True
    no_quality_gate_override: bool = True
    no_kernel_mutation: bool = True

    def __post_init__(self) -> None:
        for name in (
            "planner_consumable",
            "replayable",
            "rollback_audit_bound",
            "no_second_runtime",
            "no_direct_execution",
            "no_rollback_execution",
            "no_tool_dispatch",
            "no_budget_mutation",
            "no_quality_gate_override",
            "no_kernel_mutation",
        ):
            ensure_bool(getattr(self, name), f"RollbackAuditBindingReport.{name}")
        if not all(
            (
                self.planner_consumable,
                self.replayable,
                self.rollback_audit_bound,
                self.no_second_runtime,
                self.no_direct_execution,
                self.no_rollback_execution,
                self.no_tool_dispatch,
                self.no_budget_mutation,
                self.no_quality_gate_override,
                self.no_kernel_mutation,
            )
        ):
            raise ValueError("RollbackAuditBindingReport must remain governed projection")

    @property
    def report_digest(self) -> str:
        return stable_digest(
            {
                "ledger": self.state_delta_ledger.ledger_digest,
                "graph": self.dependency_graph.graph_digest,
                "checkpoint": self.recovery_checkpoint.public_dict().get("checkpoint_digest"),
                "envelope": self.audit_evidence_envelope.public_dict().get("evidence_digest"),
                "issues": list(self.issues),
            },
            length=24,
        )

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_45_ROLLBACK_AUDIT_SCHEMA,
            "source_version": SOURCE_VERSION,
            "report_id": sanitize_text(self.report_id, limit=240),
            "generated_at": self.generated_at,
            "status": sanitize_text(self.status, limit=120),
            "summary": self.summary_text(),
            "state_delta_ledger": self.state_delta_ledger.public_dict(),
            "dependency_graph": self.dependency_graph.public_dict(),
            "recovery_checkpoint": self.recovery_checkpoint.public_dict(),
            "audit_evidence_envelope": self.audit_evidence_envelope.public_dict(),
            "issues": [sanitize_text(item, limit=300) for item in self.issues],
            "planner_consumable": self.planner_consumable,
            "replayable": self.replayable,
            "rollback_audit_bound": self.rollback_audit_bound,
            "no_second_runtime": self.no_second_runtime,
            "no_direct_execution": self.no_direct_execution,
            "no_rollback_execution": self.no_rollback_execution,
            "no_tool_dispatch": self.no_tool_dispatch,
            "no_budget_mutation": self.no_budget_mutation,
            "no_quality_gate_override": self.no_quality_gate_override,
            "no_kernel_mutation": self.no_kernel_mutation,
            "report_digest": self.report_digest,
        }

    def summary_text(self) -> str:
        return sanitize_text(
            "L6.45回滚审计绑定："
            f"status={self.status}; deltas={len(self.state_delta_ledger.deltas)}; "
            f"deps={len(self.dependency_graph.edges)}; missing_deps={len(self.dependency_graph.missing_dependency_refs)}; "
            f"checkpoint={self.recovery_checkpoint.checkpoint_id}; audit_refs={len(self.audit_evidence_envelope.audit_refs)}; "
            "只做ref/digest绑定，不执行回滚、不调工具、不改核心。",
            limit=900,
        )


def build_state_delta_ledger(report: Any) -> StateDeltaLedger:
    payload = _payload_of(report)
    source_digest = _report_digest(payload)
    deltas: list[StateDeltaRecord] = []
    for index, record in enumerate(_step_records(payload), start=1):
        step_id = sanitize_text(record.get("step_id") or f"step_{index}", limit=160)
        tool_name = sanitize_text(record.get("tool_name") or "unknown_tool", limit=160)
        state = sanitize_text(record.get("state") or record.get("result_status") or "skipped", limit=80)
        if state not in TERMINAL_STATES:
            state = "skipped"
        audit_ref = sanitize_text(record.get("audit_ref"), limit=160)
        evidence_refs = tuple(sanitize_text(item, limit=200) for item in list(record.get("evidence_refs") or [])[:8])
        argument_digest = sanitize_text(record.get("arguments_digest"), limit=80)
        summary = sanitize_text(record.get("output_summary") or record.get("reason") or state, limit=420)
        irreversible = _is_irreversible(tool_name, str(record.get("reason") or ""), summary)
        reversible = state in {"succeeded", "recovered"} and not irreversible
        rollback_strategy = "restore_checkpoint" if reversible else "manual_review_required"
        rollback_hint = "可通过最近检查点恢复并重新验证。" if reversible else "需人工复核，禁止自动回滚。"
        delta_id = _safe_ref("delta:l6_45", source_digest, step_id, index, limit=240)
        deltas.append(
            StateDeltaRecord(
                delta_id=delta_id,
                step_id=step_id,
                tool_name=tool_name,
                state=state,
                audit_ref=audit_ref,
                before_ref=_safe_ref("state_before", source_digest, step_id, limit=200),
                after_ref=_safe_ref("state_after", source_digest, step_id, state, limit=200),
                argument_digest=argument_digest,
                evidence_refs=evidence_refs,
                artifact_refs=evidence_refs,
                changes_summary=summary,
                reversible=reversible,
                rollback_strategy=rollback_strategy,
                rollback_hint=rollback_hint,
                risk_level=sanitize_text(record.get("risk_level"), limit=80),
                error_code=sanitize_text(record.get("error_code"), limit=120),
                source_digest=source_digest,
            )
        )
    return StateDeltaLedger(
        ledger_id=_safe_ref("state_delta_ledger:l6_45", source_digest, limit=240),
        source_report_digest=source_digest,
        deltas=tuple(deltas),
    )


def build_tool_dependency_graph(report: Any, *, explicit_dependencies: dict[str, Iterable[str]] | None = None) -> ToolDependencyGraph:
    payload = _payload_of(report)
    source_digest = _report_digest(payload)
    records = _step_records(payload)
    explicit_dependencies = explicit_dependencies or {}
    nodes: list[ToolDependencyNode] = []
    edges: list[ToolDependencyEdge] = []
    known_step_ids: set[str] = set()
    failed_step_ids: list[str] = []
    blocked_step_ids: list[str] = []

    for index, record in enumerate(records, start=1):
        step_id = sanitize_text(record.get("step_id") or f"step_{index}", limit=160)
        known_step_ids.add(step_id)
        state = sanitize_text(record.get("state") or "planned", limit=80)
        if state in {"failed", "timeout"}:
            failed_step_ids.append(step_id)
        if state in {"blocked", "confirmation_required"}:
            blocked_step_ids.append(step_id)
        nodes.append(
            ToolDependencyNode(
                node_id=_safe_ref("dep_node:l6_45", source_digest, step_id, limit=200),
                step_id=step_id,
                tool_name=sanitize_text(record.get("tool_name") or "unknown_tool", limit=160),
                state=state,
                audit_ref=sanitize_text(record.get("audit_ref"), limit=160),
                delta_ref=_safe_ref("delta:l6_45", source_digest, step_id, index, limit=220),
            )
        )

    missing: list[str] = []
    for index, record in enumerate(records, start=1):
        step_id = sanitize_text(record.get("step_id") or f"step_{index}", limit=160)
        dependencies: list[str] = []
        parent_step_id = sanitize_text(record.get("parent_step_id"), limit=160)
        if parent_step_id:
            dependencies.append(parent_step_id)
        for dep in explicit_dependencies.get(step_id, ()):
            dependencies.append(sanitize_text(dep, limit=160))
        for dep in dependencies:
            if not dep:
                continue
            if dep not in known_step_ids:
                missing.append(_safe_ref("missing_dep", step_id, dep, limit=200))
                continue
            edges.append(
                ToolDependencyEdge(
                    edge_id=_safe_ref("dep_edge:l6_45", dep, step_id, len(edges) + 1, limit=200),
                    from_step_id=dep,
                    to_step_id=step_id,
                )
            )

    return ToolDependencyGraph(
        graph_id=_safe_ref("tool_dependency_graph:l6_45", source_digest, limit=240),
        source_report_digest=source_digest,
        nodes=tuple(nodes),
        edges=tuple(edges),
        missing_dependency_refs=tuple(missing),
        failed_step_ids=tuple(failed_step_ids),
        blocked_step_ids=tuple(blocked_step_ids),
    )


def build_recovery_checkpoint(
    report: Any,
    *,
    ledger: StateDeltaLedger | None = None,
    dependency_graph: ToolDependencyGraph | None = None,
) -> RecoveryCheckpoint:
    payload = _payload_of(report)
    source_digest = _report_digest(payload)
    ledger = ledger or build_state_delta_ledger(payload)
    dependency_graph = dependency_graph or build_tool_dependency_graph(payload)
    records = _step_records(payload)
    succeeded = [record for record in records if record.get("state") in {"succeeded", "recovered"}]
    last_completed = sanitize_text((succeeded[-1].get("step_id") if succeeded else "") if succeeded else "", limit=160)
    resume = dict(payload.get("resume_envelope") or {})
    next_ids = list(resume.get("next_step_ids") or [])
    next_step_id = sanitize_text(next_ids[0] if next_ids else "", limit=160)
    can_resume = bool(resume.get("can_resume", True))
    has_manual_review = ledger.manual_review_delta_count > 0 or bool(dependency_graph.missing_dependency_refs)
    rollback_required = bool(payload.get("failed_steps") or payload.get("blocked_steps") or payload.get("timeout_steps") or has_manual_review)
    audit_refs = tuple(delta.audit_ref for delta in ledger.deltas if delta.audit_ref)
    state_delta_refs = tuple(delta.delta_id for delta in ledger.deltas)
    checkpoint_payload = {
        "source_report_digest": source_digest,
        "last_completed_step_id": last_completed,
        "next_step_id": next_step_id,
        "state_delta_refs": list(state_delta_refs),
        "audit_refs": list(audit_refs),
        "dependency_graph": dependency_graph.graph_digest,
    }
    checkpoint_digest = stable_digest(checkpoint_payload, length=24)
    return RecoveryCheckpoint(
        checkpoint_id=_safe_ref("recovery_checkpoint:l6_45", source_digest, checkpoint_digest, limit=240),
        source_report_digest=source_digest,
        last_completed_step_id=last_completed,
        next_step_id=next_step_id,
        resume_mode=sanitize_text(resume.get("resume_mode") or "resume_from_next_step", limit=120),
        can_resume=can_resume,
        rollback_required=rollback_required,
        rollback_plan_ref=_safe_ref("rollback_plan_review", source_digest, checkpoint_digest, limit=220) if rollback_required else "",
        validation_required=True,
        state_delta_refs=state_delta_refs,
        audit_refs=audit_refs,
        dependency_graph_ref=dependency_graph.graph_id,
        checkpoint_digest=checkpoint_digest,
    )


def build_audit_evidence_envelope(
    report: Any,
    *,
    ledger: StateDeltaLedger | None = None,
    dependency_graph: ToolDependencyGraph | None = None,
    checkpoint: RecoveryCheckpoint | None = None,
) -> AuditEvidenceEnvelope:
    payload = _payload_of(report)
    source_digest = _report_digest(payload)
    ledger = ledger or build_state_delta_ledger(payload)
    dependency_graph = dependency_graph or build_tool_dependency_graph(payload)
    checkpoint = checkpoint or build_recovery_checkpoint(payload, ledger=ledger, dependency_graph=dependency_graph)
    audit_refs = tuple(delta.audit_ref for delta in ledger.deltas if delta.audit_ref)
    state_delta_refs = tuple(delta.delta_id for delta in ledger.deltas)
    summary = (
        f"绑定 {len(state_delta_refs)} 条状态变化、{len(audit_refs)} 条审计引用、"
        f"{len(dependency_graph.edges)} 条依赖边；checkpoint={checkpoint.checkpoint_id}。"
    )
    evidence_digest = stable_digest(
        {
            "audit_refs": list(audit_refs),
            "state_delta_refs": list(state_delta_refs),
            "dependency_graph": dependency_graph.graph_digest,
            "checkpoint": checkpoint.public_dict().get("checkpoint_digest"),
        },
        length=24,
    )
    return AuditEvidenceEnvelope(
        envelope_id=_safe_ref("audit_evidence_envelope:l6_45", source_digest, evidence_digest, limit=240),
        source_report_digest=source_digest,
        audit_refs=audit_refs,
        state_delta_refs=state_delta_refs,
        dependency_graph_ref=dependency_graph.graph_id,
        recovery_checkpoint_ref=checkpoint.checkpoint_id,
        evidence_digest=evidence_digest,
        summary=summary,
    )


def build_rollback_audit_binding_report(
    report: Any,
    *,
    explicit_dependencies: dict[str, Iterable[str]] | None = None,
) -> RollbackAuditBindingReport:
    payload = _payload_of(report)
    source_digest = _report_digest(payload)
    ledger = build_state_delta_ledger(payload)
    graph = build_tool_dependency_graph(payload, explicit_dependencies=explicit_dependencies)
    checkpoint = build_recovery_checkpoint(payload, ledger=ledger, dependency_graph=graph)
    envelope = build_audit_evidence_envelope(payload, ledger=ledger, dependency_graph=graph, checkpoint=checkpoint)
    issues: list[str] = []
    if graph.missing_dependency_refs:
        issues.append("dependency_missing_review_required")
    if ledger.manual_review_delta_count:
        issues.append("manual_rollback_review_required")
    if checkpoint.rollback_required:
        issues.append("rollback_or_resume_validation_required")
    status = "ready_with_review" if issues else "ready"
    return RollbackAuditBindingReport(
        report_id=_safe_ref("rollback_audit_binding_report:l6_45", source_digest, limit=240),
        status=status,
        state_delta_ledger=ledger,
        dependency_graph=graph,
        recovery_checkpoint=checkpoint,
        audit_evidence_envelope=envelope,
        issues=tuple(issues),
    )
