"""L6.42.1 自我迭代前端投影与用户确认票据。

前端“自我迭代区”只展示候选、风险、范围、测试与回滚要求。用户确认后
生成 UserConfirmedIterationTicket。票据只允许 Planner 生成改造计划，不允许
直接 patch、合入、热切换或改核心组。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any
import hashlib
import json

from tiangong_kernel.l6_plugins.common._common import ensure_bool

from .self_iteration_route import SelfIterationRoute

L6_42_1_SELF_ITERATION_FRONTEND_SCHEMA = "tiangong.l6_42_1.self_iteration_frontend_projection.v1"
RISK_LEVELS = {"A0", "A1", "A2", "A3", "A4", "A5"}


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
class SelfIterationFrontendItem:
    item_id: str
    discovered_need_summary: str
    proposed_change_summary: str
    estimated_scope: str = "runtime_shell_or_frontend_projection"
    risk_level: str = "A3"
    source_refs: list[str] = field(default_factory=list)
    validation_refs: list[str] = field(default_factory=list)
    rollback_plan_ref: str = "rollback:l6_42_1_required"
    requires_user_confirmation: bool = True
    user_confirmed: bool = False
    frontend_visible: bool = True
    projection_only: bool = True
    no_direct_execution: bool = True
    no_patch_apply: bool = True
    no_merge: bool = True
    no_hot_switch: bool = True
    no_core_mutation: bool = True
    applies_patch: bool = False
    merges_change: bool = False
    performs_hot_switch: bool = False
    mutates_core: bool = False

    def __post_init__(self) -> None:
        if not _text(self.item_id, 240):
            raise ValueError("SelfIterationFrontendItem.item_id must be non-empty text")
        if self.risk_level not in RISK_LEVELS:
            raise ValueError("SelfIterationFrontendItem.risk_level is invalid")
        for field_name in (
            "requires_user_confirmation",
            "user_confirmed",
            "frontend_visible",
            "projection_only",
            "no_direct_execution",
            "no_patch_apply",
            "no_merge",
            "no_hot_switch",
            "no_core_mutation",
            "applies_patch",
            "merges_change",
            "performs_hot_switch",
            "mutates_core",
        ):
            ensure_bool(getattr(self, field_name), f"SelfIterationFrontendItem.{field_name}")
        if not (self.frontend_visible and self.projection_only and self.no_direct_execution and self.no_patch_apply and self.no_merge and self.no_hot_switch and self.no_core_mutation):
            raise ValueError("SelfIterationFrontendItem must remain projection-only")
        if self.applies_patch or self.merges_change or self.performs_hot_switch or self.mutates_core:
            raise ValueError("SelfIterationFrontendItem cannot execute iteration side effects")

    def public_dict(self) -> dict[str, Any]:
        return {
            "item_id": _text(self.item_id, 240),
            "discovered_need_summary": _text(self.discovered_need_summary, 600),
            "proposed_change_summary": _text(self.proposed_change_summary, 600),
            "estimated_scope": _text(self.estimated_scope, 240),
            "risk_level": self.risk_level,
            "source_refs": [_text(item, 240) for item in self.source_refs[:10]],
            "validation_refs": [_text(item, 240) for item in self.validation_refs[:10]],
            "rollback_plan_ref": _text(self.rollback_plan_ref, 240),
            "requires_user_confirmation": self.requires_user_confirmation,
            "user_confirmed": self.user_confirmed,
            "frontend_visible": self.frontend_visible,
            "projection_only": self.projection_only,
            "no_direct_execution": self.no_direct_execution,
            "no_patch_apply": self.no_patch_apply,
            "no_merge": self.no_merge,
            "no_hot_switch": self.no_hot_switch,
            "no_core_mutation": self.no_core_mutation,
            "applies_patch": self.applies_patch,
            "merges_change": self.merges_change,
            "performs_hot_switch": self.performs_hot_switch,
            "mutates_core": self.mutates_core,
        }


@dataclass(frozen=True)
class SelfIterationFrontendProjection:
    projection_id: str
    items: list[SelfIterationFrontendItem] = field(default_factory=list)
    generated_at: float = field(default_factory=time)
    display_zone_name: str = "自我迭代区"
    user_review_required: bool = True
    frontend_projection_only: bool = True
    planner_consumable: bool = True
    no_direct_execution: bool = True
    no_patch_apply: bool = True
    no_hot_switch: bool = True
    no_core_mutation: bool = True
    invokes_tool: bool = False
    applies_patch: bool = False
    performs_hot_switch: bool = False
    mutates_core: bool = False

    def __post_init__(self) -> None:
        if not _text(self.projection_id, 240):
            raise ValueError("SelfIterationFrontendProjection.projection_id must be non-empty text")
        for field_name in (
            "user_review_required",
            "frontend_projection_only",
            "planner_consumable",
            "no_direct_execution",
            "no_patch_apply",
            "no_hot_switch",
            "no_core_mutation",
            "invokes_tool",
            "applies_patch",
            "performs_hot_switch",
            "mutates_core",
        ):
            ensure_bool(getattr(self, field_name), f"SelfIterationFrontendProjection.{field_name}")
        if not (self.user_review_required and self.frontend_projection_only and self.planner_consumable and self.no_direct_execution and self.no_patch_apply and self.no_hot_switch and self.no_core_mutation):
            raise ValueError("SelfIterationFrontendProjection must remain front-end projection only")
        if self.invokes_tool or self.applies_patch or self.performs_hot_switch or self.mutates_core:
            raise ValueError("SelfIterationFrontendProjection cannot execute iteration side effects")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_42_1_SELF_ITERATION_FRONTEND_SCHEMA,
            "projection_id": _text(self.projection_id, 240),
            "generated_at": self.generated_at,
            "display_zone_name": _text(self.display_zone_name, 80),
            "items": [item.public_dict() for item in self.items[:12]],
            "user_review_required": self.user_review_required,
            "frontend_projection_only": self.frontend_projection_only,
            "planner_consumable": self.planner_consumable,
            "no_direct_execution": self.no_direct_execution,
            "no_patch_apply": self.no_patch_apply,
            "no_hot_switch": self.no_hot_switch,
            "no_core_mutation": self.no_core_mutation,
            "invokes_tool": self.invokes_tool,
            "applies_patch": self.applies_patch,
            "performs_hot_switch": self.performs_hot_switch,
            "mutates_core": self.mutates_core,
        }


@dataclass(frozen=True)
class UserConfirmedIterationTicket:
    ticket_id: str
    item_id: str
    confirmed_by_user: bool = True
    confirmation_note: str = "用户确认进入自我迭代计划生成"
    permits_planner_draft_generation: bool = True
    permits_execution: bool = False
    requires_quality_gate: bool = True
    requires_rollback_checkpoint: bool = True
    requires_core_pollution_check: bool = True
    no_patch_apply: bool = True
    no_merge: bool = True
    no_hot_switch: bool = True
    no_core_mutation: bool = True
    applies_patch: bool = False
    merges_change: bool = False
    performs_hot_switch: bool = False
    mutates_core: bool = False

    def __post_init__(self) -> None:
        if not _text(self.ticket_id, 240):
            raise ValueError("UserConfirmedIterationTicket.ticket_id must be non-empty text")
        if not _text(self.item_id, 240):
            raise ValueError("UserConfirmedIterationTicket.item_id must be non-empty text")
        for field_name in (
            "confirmed_by_user",
            "permits_planner_draft_generation",
            "permits_execution",
            "requires_quality_gate",
            "requires_rollback_checkpoint",
            "requires_core_pollution_check",
            "no_patch_apply",
            "no_merge",
            "no_hot_switch",
            "no_core_mutation",
            "applies_patch",
            "merges_change",
            "performs_hot_switch",
            "mutates_core",
        ):
            ensure_bool(getattr(self, field_name), f"UserConfirmedIterationTicket.{field_name}")
        if not (self.confirmed_by_user and self.permits_planner_draft_generation and self.requires_quality_gate and self.requires_rollback_checkpoint and self.requires_core_pollution_check and self.no_patch_apply and self.no_merge and self.no_hot_switch and self.no_core_mutation):
            raise ValueError("UserConfirmedIterationTicket must remain gated planner ticket")
        if self.permits_execution or self.applies_patch or self.merges_change or self.performs_hot_switch or self.mutates_core:
            raise ValueError("UserConfirmedIterationTicket cannot execute iteration side effects")

    def public_dict(self) -> dict[str, Any]:
        return {
            "ticket_id": _text(self.ticket_id, 240),
            "item_id": _text(self.item_id, 240),
            "confirmed_by_user": self.confirmed_by_user,
            "confirmation_note": _text(self.confirmation_note, 360),
            "permits_planner_draft_generation": self.permits_planner_draft_generation,
            "permits_execution": self.permits_execution,
            "requires_quality_gate": self.requires_quality_gate,
            "requires_rollback_checkpoint": self.requires_rollback_checkpoint,
            "requires_core_pollution_check": self.requires_core_pollution_check,
            "no_patch_apply": self.no_patch_apply,
            "no_merge": self.no_merge,
            "no_hot_switch": self.no_hot_switch,
            "no_core_mutation": self.no_core_mutation,
            "applies_patch": self.applies_patch,
            "merges_change": self.merges_change,
            "performs_hot_switch": self.performs_hot_switch,
            "mutates_core": self.mutates_core,
        }


def build_self_iteration_frontend_projection(
    *,
    iteration_route: SelfIterationRoute,
    conversation_need_refs: list[str] | None = None,
    user_feedback_refs: list[str] | None = None,
    notes: str = "",
) -> SelfIterationFrontendProjection:
    refs = list(iteration_route.proposal_refs or []) + list(iteration_route.change_candidate_refs or []) + list(conversation_need_refs or []) + list(user_feedback_refs or [])
    if not refs and notes:
        refs.append(f"conversation_need:l6_42_1_{_digest(notes)}")
    if not refs:
        refs.append("conversation_need:l6_42_1_default_review")
    items: list[SelfIterationFrontendItem] = []
    for idx, ref in enumerate(refs[:6]):
        items.append(
            SelfIterationFrontendItem(
                item_id=f"iteration_frontend_item:{_digest([iteration_route.route_id, ref, idx])}",
                discovered_need_summary=f"从日常沟通/执行反馈中沉淀的改进需求：{_text(ref, 180)}",
                proposed_change_summary="生成改进方案草案，先展示给用户确认；确认后才允许 Planner 生成执行计划。",
                estimated_scope="runtime_shell_or_frontend_projection；禁止默认修改核心组",
                risk_level="A3",
                source_refs=[ref, iteration_route.route_id],
                validation_refs=iteration_route.validation_requirement_refs or ["validation:l6_42_1_iteration_required"],
                rollback_plan_ref=(iteration_route.rollback_requirement_refs[0] if iteration_route.rollback_requirement_refs else "rollback:l6_42_1_iteration_required"),
            )
        )
    return SelfIterationFrontendProjection(
        projection_id=f"iteration_frontend_projection:{_digest([iteration_route.public_dict(), refs, notes])}",
        items=items,
    )


def build_user_confirmed_iteration_ticket(*, item: SelfIterationFrontendItem, confirmation_note: str = "用户确认") -> UserConfirmedIterationTicket:
    return UserConfirmedIterationTicket(
        ticket_id=f"iteration_confirm_ticket:{_digest([item.public_dict(), confirmation_note])}",
        item_id=item.item_id,
        confirmation_note=confirmation_note,
    )
