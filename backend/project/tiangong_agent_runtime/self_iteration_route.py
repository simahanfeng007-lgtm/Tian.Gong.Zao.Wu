"""L6.42 SelfIteration 接入路由。

自我迭代只生成改进候选、patch 草案意图、验证需求和回滚需求。它不能自动
合入、不能热切换、不能改版本槽、不能写核心、不能绕过质量门。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any
import hashlib
import json

from tiangong_kernel.l6_plugins.common._common import ensure_bool, ensure_score

L6_42_SELF_ITERATION_SCHEMA = "tiangong.l6_42.self_iteration_route.v1"


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


@dataclass(frozen=True)
class SelfIterationRoute:
    """Planner 可消费的自我迭代候选路由。"""

    route_id: str
    generated_at: float = field(default_factory=time)
    iteration_need_score: float = 0.0
    proposal_refs: list[str] = field(default_factory=list)
    change_candidate_refs: list[str] = field(default_factory=list)
    version_slot_candidate_refs: list[str] = field(default_factory=list)
    validation_requirement_refs: list[str] = field(default_factory=list)
    rollback_requirement_refs: list[str] = field(default_factory=list)
    planner_hint: str = ""
    priority: str = "P4_iteration_after_stability"
    planner_consumable: bool = True
    candidate_only: bool = True
    quality_gate_required: bool = True
    rollback_required: bool = True
    no_direct_execution: bool = True
    no_patch_apply: bool = True
    no_merge: bool = True
    no_hot_switch: bool = True
    no_version_activation: bool = True
    no_file_write: bool = True
    no_tool_invocation: bool = True
    no_kernel_mutation: bool = True
    applies_patch: bool = False
    merges_change: bool = False
    performs_hot_switch: bool = False
    activates_version_slot: bool = False
    writes_file: bool = False
    invokes_tool: bool = False
    mutates_kernel: bool = False

    def __post_init__(self) -> None:
        if not _text(self.route_id, 240):
            raise ValueError("SelfIterationRoute.route_id must be non-empty text")
        ensure_score(self.iteration_need_score, "SelfIterationRoute.iteration_need_score")
        for field_name in (
            "planner_consumable",
            "candidate_only",
            "quality_gate_required",
            "rollback_required",
            "no_direct_execution",
            "no_patch_apply",
            "no_merge",
            "no_hot_switch",
            "no_version_activation",
            "no_file_write",
            "no_tool_invocation",
            "no_kernel_mutation",
            "applies_patch",
            "merges_change",
            "performs_hot_switch",
            "activates_version_slot",
            "writes_file",
            "invokes_tool",
            "mutates_kernel",
        ):
            ensure_bool(getattr(self, field_name), f"SelfIterationRoute.{field_name}")
        required = (
            self.planner_consumable,
            self.candidate_only,
            self.quality_gate_required,
            self.rollback_required,
            self.no_direct_execution,
            self.no_patch_apply,
            self.no_merge,
            self.no_hot_switch,
            self.no_version_activation,
            self.no_file_write,
            self.no_tool_invocation,
            self.no_kernel_mutation,
        )
        if not all(required):
            raise ValueError("SelfIterationRoute must remain candidate-only and gate-routed")
        forbidden = (
            self.applies_patch,
            self.merges_change,
            self.performs_hot_switch,
            self.activates_version_slot,
            self.writes_file,
            self.invokes_tool,
            self.mutates_kernel,
        )
        if any(forbidden):
            raise ValueError("SelfIterationRoute cannot execute iteration side effects")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_42_SELF_ITERATION_SCHEMA,
            "route_id": _text(self.route_id, 240),
            "generated_at": self.generated_at,
            "iteration_need_score": self.iteration_need_score,
            "proposal_refs": [_text(item, 240) for item in self.proposal_refs],
            "change_candidate_refs": [_text(item, 240) for item in self.change_candidate_refs],
            "version_slot_candidate_refs": [_text(item, 240) for item in self.version_slot_candidate_refs],
            "validation_requirement_refs": [_text(item, 240) for item in self.validation_requirement_refs],
            "rollback_requirement_refs": [_text(item, 240) for item in self.rollback_requirement_refs],
            "planner_hint": _text(self.planner_hint, 900),
            "priority": self.priority,
            "planner_consumable": self.planner_consumable,
            "candidate_only": self.candidate_only,
            "quality_gate_required": self.quality_gate_required,
            "rollback_required": self.rollback_required,
            "no_direct_execution": self.no_direct_execution,
            "no_patch_apply": self.no_patch_apply,
            "no_merge": self.no_merge,
            "no_hot_switch": self.no_hot_switch,
            "no_version_activation": self.no_version_activation,
            "no_file_write": self.no_file_write,
            "no_tool_invocation": self.no_tool_invocation,
            "no_kernel_mutation": self.no_kernel_mutation,
            "applies_patch": self.applies_patch,
            "merges_change": self.merges_change,
            "performs_hot_switch": self.performs_hot_switch,
            "activates_version_slot": self.activates_version_slot,
            "writes_file": self.writes_file,
            "invokes_tool": self.invokes_tool,
            "mutates_kernel": self.mutates_kernel,
        }


def build_self_iteration_route(
    *,
    iteration_candidates: list[Any] | None = None,
    repeated_failure_count: int = 0,
    user_confirmed_direction: bool = False,
    notes: str = "",
) -> SelfIterationRoute:
    if isinstance(repeated_failure_count, bool) or not isinstance(repeated_failure_count, int) or repeated_failure_count < 0:
        raise ValueError("repeated_failure_count must be non-negative int")
    proposals: list[str] = []
    changes: list[str] = []
    version_slots: list[str] = []
    for item in (iteration_candidates or [])[:8]:
        ref = getattr(item, "object_ref", None) or getattr(item, "output_ref", None) or str(item)
        safe = _text(ref, 180)
        if "version" in safe or "slot" in safe or "hotswitch" in safe:
            version_slots.append(safe)
        elif "change" in safe or "patch" in safe:
            changes.append(safe)
        else:
            proposals.append(safe)
    if notes and not proposals:
        proposals.append(f"suggestion:l6_42_iteration_{_digest(notes)}")
    need = min(1.0, 0.14 * repeated_failure_count + 0.18 * bool(proposals or changes or version_slots) + 0.18 * bool(user_confirmed_direction))
    hint = "SelfIteration 接入：只生成改进候选、验证需求和回滚需求；patch 草案可后续经 Planner Step 生成，合入/热切换必须过质量门。"
    if user_confirmed_direction:
        hint += " 用户已确认改进方向，可提升候选排序但仍不自动合入。"
    elif notes:
        hint += f" 备注：{_text(notes, 180)}"
    return SelfIterationRoute(
        route_id=f"iteration_route:{_digest([proposals, changes, version_slots, repeated_failure_count, user_confirmed_direction, notes])}",
        iteration_need_score=need,
        proposal_refs=proposals[:6],
        change_candidate_refs=changes[:6],
        version_slot_candidate_refs=version_slots[:4],
        validation_requirement_refs=["validation:l6_42_iteration_required"] if need > 0 else [],
        rollback_requirement_refs=["rollback:l6_42_iteration_required"] if need > 0 else [],
        planner_hint=hint,
        priority="P2_user_confirmed_iteration" if user_confirmed_direction else "P4_iteration_after_stability",
    )
