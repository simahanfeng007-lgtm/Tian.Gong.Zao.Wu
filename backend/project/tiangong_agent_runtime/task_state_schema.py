"""L6.72.53 任务级状态账本 schema。

第一版为记录层：不改变 Runtime 执行决策，只补足长链任务的跨轮证据、
阶段、状态和续接底座。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from tiangong_agent_shell.safe_logging import redact_text


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_task_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"task_{stamp}_{uuid4().hex[:10]}"


def safe_preview(value: Any, limit: int = 600) -> str:
    return redact_text(str(value or ""))[: max(1, int(limit))]


def json_safe(value: Any, *, depth: int = 4) -> Any:
    if depth <= 0:
        return safe_preview(value, 160)
    if value is None or isinstance(value, (bool, int, float, str)):
        return safe_preview(value, 2000) if isinstance(value, str) else value
    if isinstance(value, dict):
        return {safe_preview(k, 80): json_safe(v, depth=depth - 1) for k, v in list(value.items())[:80]}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(v, depth=depth - 1) for v in list(value)[:120]]
    if hasattr(value, "public_dict"):
        try:
            return json_safe(value.public_dict(), depth=depth - 1)
        except Exception:  # noqa: BLE001
            return safe_preview(value, 300)
    return safe_preview(value, 300)


@dataclass
class TaskEvent:
    event_id: str
    task_id: str
    event_type: str
    created_at: str
    payload: dict[str, Any] = field(default_factory=dict)

    def public_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "task_id": self.task_id,
            "event_type": self.event_type,
            "created_at": self.created_at,
            "payload": json_safe(self.payload),
        }


@dataclass
class TaskState:
    task_id: str
    created_at: str
    updated_at: str
    user_goal: str
    normalized_goal: str = ""
    user_selected_mode: str = "work"
    activation_form: dict[str, Any] | None = None
    model_profile_ref: str = ""
    model_profile: dict[str, Any] | None = None
    model_execution_policy: dict[str, Any] | None = None
    active_model_policy: dict[str, Any] | None = None
    current_phase: str = "created"
    current_subgoal: str = ""
    status: str = "created"
    completion_criteria: list[str] = field(default_factory=list)
    plan_history: list[dict[str, Any]] = field(default_factory=list)
    current_plan: list[dict[str, Any]] = field(default_factory=list)
    executed_steps: list[dict[str, Any]] = field(default_factory=list)
    evidence_refs: list[dict[str, Any]] = field(default_factory=list)
    artifact_refs: list[dict[str, Any]] = field(default_factory=list)
    quality_gate: dict[str, Any] | None = None
    unresolved_failures: list[dict[str, Any]] = field(default_factory=list)
    recovery_plan: dict[str, Any] | None = None
    retry_budget: dict[str, Any] = field(default_factory=lambda: {"max_retries": 2, "used": 0})
    context_packs: list[dict[str, Any]] = field(default_factory=list)
    playbook_routes: list[dict[str, Any]] = field(default_factory=list)
    tool_budget: dict[str, Any] = field(default_factory=dict)
    token_budget: dict[str, Any] = field(default_factory=dict)
    write_budget: dict[str, Any] = field(default_factory=dict)
    rollback_checkpoints: list[dict[str, Any]] = field(default_factory=list)
    next_action: str = ""
    final_output_contract: str = "execution_report"
    learning_candidates: list[dict[str, Any]] = field(default_factory=list)
    audit_refs: list[dict[str, Any]] = field(default_factory=list)
    passive_only: bool = True

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": "tiangong.l6_72_53.task_state.v1",
            "task_id": self.task_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "user_goal": safe_preview(self.user_goal, 1200),
            "normalized_goal": safe_preview(self.normalized_goal, 1200),
            "user_selected_mode": self.user_selected_mode,
            "activation_form": json_safe(self.activation_form),
            "model_profile_ref": self.model_profile_ref,
            "model_profile": json_safe(self.model_profile),
            "model_execution_policy": json_safe(self.model_execution_policy),
            "active_model_policy": json_safe(self.active_model_policy),
            "current_phase": self.current_phase,
            "current_subgoal": safe_preview(self.current_subgoal, 600),
            "status": self.status,
            "completion_criteria": json_safe(self.completion_criteria),
            "plan_history": json_safe(self.plan_history),
            "current_plan": json_safe(self.current_plan),
            "executed_steps": json_safe(self.executed_steps),
            "evidence_refs": json_safe(self.evidence_refs),
            "artifact_refs": json_safe(self.artifact_refs),
            "quality_gate": json_safe(self.quality_gate),
            "unresolved_failures": json_safe(self.unresolved_failures),
            "recovery_plan": json_safe(self.recovery_plan),
            "retry_budget": json_safe(self.retry_budget),
            "context_packs": json_safe(self.context_packs),
            "playbook_routes": json_safe(self.playbook_routes),
            "tool_budget": json_safe(self.tool_budget),
            "token_budget": json_safe(self.token_budget),
            "write_budget": json_safe(self.write_budget),
            "rollback_checkpoints": json_safe(self.rollback_checkpoints),
            "next_action": safe_preview(self.next_action, 600),
            "final_output_contract": self.final_output_contract,
            "learning_candidates": json_safe(self.learning_candidates),
            "audit_refs": json_safe(self.audit_refs),
            "storage_boundary": {
                "no_api_key": True,
                "no_full_file_content": True,
                "summary_and_refs_only": True,
                "context_packs_summary_only": True,
                "playbook_routes_summary_only": True,
                "active_model_policy_summary_only": True,
                "passive_only": self.passive_only,
            },
        }
