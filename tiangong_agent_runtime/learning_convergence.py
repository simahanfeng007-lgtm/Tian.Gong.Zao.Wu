"""L6.28 经验 / Skill / Tool 候选执行合流外壳。

L6.20-L6.23 已经能把执行结果沉淀为经验、Skill 草案、Tool 生产请求和
LLM 外骨骼压缩结果。本模块只做下一步：把这些对象合流为 Planner 可直接消费
的执行卡片与路由，不再停留在报告层。

边界：本模块不写正式记忆、不写 Skill 注册表、不激活 Skill、不生产真实 Tool、
不写工具代码、不释放工具句柄、不修改 tiangong_kernel。质量门只卡正式注册、
激活、发布和 A5 高危；A0-A4 草案、提示、合流和续接默认放行。
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

LEARNING_CONVERGENCE_SCHEMA = "tiangong.l6_28.learning_convergence.v1"
SENSITIVE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer|token|secret|password|credential)\s*[:=]\s*[^\s,;]+"
)
SENSITIVE_WORDS = ("api_key", "apikey", "authorization", "bearer", "token", "secret", "password", "credential")


@dataclass(frozen=True)
class LearningSourceRef:
    """合流输入源摘要，只保留安全引用和计数。"""

    source_ref: str
    source_schema: str
    source_kind: str
    status: str
    item_count: int
    contributes_to: list[str] = field(default_factory=list)

    def public_dict(self) -> dict[str, Any]:
        return {
            "source_ref": self.source_ref,
            "source_schema": self.source_schema,
            "source_kind": self.source_kind,
            "status": self.status,
            "item_count": self.item_count,
            "contributes_to": list(self.contributes_to),
        }


@dataclass(frozen=True)
class PlannerHintRoute:
    """Planner 可直接消费的执行提示路由。"""

    route_ref: str
    source_ref: str
    title: str
    trigger: str
    action_hint: str
    priority: str = "P1_execution"
    consumption_mode: str = "prepend_to_next_planner_context"
    already_actionable: bool = True
    writes_memory: bool = False
    writes_skill_registry: bool = False
    activates_skill: bool = False
    applies_change: bool = False

    def __post_init__(self) -> None:
        if not self.already_actionable:
            raise ValueError("L6.28 PlannerHintRoute must be immediately actionable")
        if self.writes_memory or self.writes_skill_registry or self.activates_skill or self.applies_change:
            raise ValueError("L6.28 PlannerHintRoute cannot write memory/registry, activate skill or apply change")

    def public_dict(self) -> dict[str, Any]:
        return {
            "route_ref": self.route_ref,
            "source_ref": self.source_ref,
            "title": self.title,
            "trigger": self.trigger,
            "action_hint": self.action_hint,
            "priority": self.priority,
            "consumption_mode": self.consumption_mode,
            "already_actionable": self.already_actionable,
            "writes_memory": self.writes_memory,
            "writes_skill_registry": self.writes_skill_registry,
            "activates_skill": self.activates_skill,
            "applies_change": self.applies_change,
        }


@dataclass(frozen=True)
class SkillDraftRoute:
    """Skill 草案到 PlannerHint 的消费路由。"""

    route_ref: str
    source_ref: str
    skill_name: str
    purpose: str
    next_use_condition: str
    planner_hint_ref: str
    can_be_consumed_as_hint: bool = True
    review_required_before_activation: bool = True
    writes_skill_registry: bool = False
    registers_skill: bool = False
    activates_skill: bool = False
    visible_capability: bool = False

    def __post_init__(self) -> None:
        if not self.can_be_consumed_as_hint or not self.review_required_before_activation:
            raise ValueError("L6.28 SkillDraftRoute must be hint-consumable but activation-gated")
        if self.writes_skill_registry or self.registers_skill or self.activates_skill or self.visible_capability:
            raise ValueError("L6.28 SkillDraftRoute cannot write/register/activate/expose Skill")

    def public_dict(self) -> dict[str, Any]:
        return {
            "route_ref": self.route_ref,
            "source_ref": self.source_ref,
            "skill_name": self.skill_name,
            "purpose": self.purpose,
            "next_use_condition": self.next_use_condition,
            "planner_hint_ref": self.planner_hint_ref,
            "can_be_consumed_as_hint": self.can_be_consumed_as_hint,
            "review_required_before_activation": self.review_required_before_activation,
            "writes_skill_registry": self.writes_skill_registry,
            "registers_skill": self.registers_skill,
            "activates_skill": self.activates_skill,
            "visible_capability": self.visible_capability,
        }


@dataclass(frozen=True)
class ToolCandidateRoute:
    """Tool 候选到最小草案 / smoke 的消费路由。"""

    route_ref: str
    source_ref: str
    tool_name: str
    purpose: str
    smoke_test: str
    next_step: str = "build_minimal_draft_and_smoke_in_sandbox"
    can_create_minimal_draft: bool = True
    sandbox_required: bool = True
    risk_level: str = "A2_convergence/A3_future_workspace_sandbox"
    produces_tool: bool = False
    writes_tool_code: bool = False
    registers_tool: bool = False
    releases_tool_handle: bool = False
    calls_tool: bool = False
    touches_kernel: bool = False

    def __post_init__(self) -> None:
        if not self.can_create_minimal_draft or not self.sandbox_required:
            raise ValueError("L6.28 ToolCandidateRoute must be draft-capable and sandbox-gated")
        forbidden = (
            self.produces_tool,
            self.writes_tool_code,
            self.registers_tool,
            self.releases_tool_handle,
            self.calls_tool,
            self.touches_kernel,
        )
        if any(forbidden):
            raise ValueError("L6.28 ToolCandidateRoute cannot produce/write/register/release/call/touch kernel")

    def public_dict(self) -> dict[str, Any]:
        return {
            "route_ref": self.route_ref,
            "source_ref": self.source_ref,
            "tool_name": self.tool_name,
            "purpose": self.purpose,
            "smoke_test": self.smoke_test,
            "next_step": self.next_step,
            "can_create_minimal_draft": self.can_create_minimal_draft,
            "sandbox_required": self.sandbox_required,
            "risk_level": self.risk_level,
            "produces_tool": self.produces_tool,
            "writes_tool_code": self.writes_tool_code,
            "registers_tool": self.registers_tool,
            "releases_tool_handle": self.releases_tool_handle,
            "calls_tool": self.calls_tool,
            "touches_kernel": self.touches_kernel,
        }


@dataclass(frozen=True)
class ExecutionConsumptionCard:
    """下一轮 Planner 直接使用的执行卡片。"""

    card_ref: str
    title: str
    consumed_refs: list[str]
    immediate_next_action: str
    expected_execution_gain: str
    quality_gate_policy: str = "gate_activation_release_not_draft_convergence"
    status: str = "ready_for_next_run"
    execution_first: bool = True
    applies_change: bool = False
    modifies_code: bool = False
    touches_kernel: bool = False

    def __post_init__(self) -> None:
        if not self.execution_first or self.status != "ready_for_next_run":
            raise ValueError("L6.28 ExecutionConsumptionCard must be execution-first and ready for next run")
        if self.applies_change or self.modifies_code or self.touches_kernel:
            raise ValueError("L6.28 ExecutionConsumptionCard cannot apply change, modify code or touch kernel")

    def public_dict(self) -> dict[str, Any]:
        return {
            "card_ref": self.card_ref,
            "title": self.title,
            "consumed_refs": list(self.consumed_refs),
            "immediate_next_action": self.immediate_next_action,
            "expected_execution_gain": self.expected_execution_gain,
            "quality_gate_policy": self.quality_gate_policy,
            "status": self.status,
            "execution_first": self.execution_first,
            "applies_change": self.applies_change,
            "modifies_code": self.modifies_code,
            "touches_kernel": self.touches_kernel,
        }


@dataclass(frozen=True)
class LearningConvergenceReport:
    schema: str
    generated_at: float
    status: str
    summary: str
    source_refs: list[LearningSourceRef] = field(default_factory=list)
    planner_hint_routes: list[PlannerHintRoute] = field(default_factory=list)
    skill_draft_routes: list[SkillDraftRoute] = field(default_factory=list)
    tool_candidate_routes: list[ToolCandidateRoute] = field(default_factory=list)
    consumption_cards: list[ExecutionConsumptionCard] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    source_schemas: list[str] = field(default_factory=list)
    notes_used: bool = False
    execution_first: bool = True
    direct_consumption: bool = True
    shell_only: bool = True
    learning_loop_closed: bool = True
    blocks_only_activation_release: bool = True
    writes_memory: bool = False
    writes_skill_registry: bool = False
    registers_skill: bool = False
    activates_skill: bool = False
    produces_tool: bool = False
    writes_tool_code: bool = False
    registers_tool: bool = False
    releases_tool_handle: bool = False
    calls_tool: bool = False
    modifies_code: bool = False
    applies_change: bool = False
    touches_kernel: bool = False
    report_digest: str = ""

    def __post_init__(self) -> None:
        required = (
            self.execution_first,
            self.direct_consumption,
            self.shell_only,
            self.learning_loop_closed,
            self.blocks_only_activation_release,
        )
        if not all(required):
            raise ValueError("L6.28 learning convergence must remain execution-first, direct, shell-only and activation-gated")
        forbidden = (
            self.writes_memory,
            self.writes_skill_registry,
            self.registers_skill,
            self.activates_skill,
            self.produces_tool,
            self.writes_tool_code,
            self.registers_tool,
            self.releases_tool_handle,
            self.calls_tool,
            self.modifies_code,
            self.applies_change,
            self.touches_kernel,
        )
        if any(forbidden):
            raise ValueError("L6.28 learning convergence cannot perform memory/skill/tool/code/kernel side effects")

    @property
    def planner_hint_count(self) -> int:
        return len(self.planner_hint_routes)

    @property
    def skill_draft_count(self) -> int:
        return len(self.skill_draft_routes)

    @property
    def tool_candidate_count(self) -> int:
        return len(self.tool_candidate_routes)

    @property
    def consumption_card_count(self) -> int:
        return len(self.consumption_cards)

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "status": self.status,
            "summary": self.summary,
            "source_refs": [item.public_dict() for item in self.source_refs],
            "planner_hint_routes": [item.public_dict() for item in self.planner_hint_routes],
            "skill_draft_routes": [item.public_dict() for item in self.skill_draft_routes],
            "tool_candidate_routes": [item.public_dict() for item in self.tool_candidate_routes],
            "consumption_cards": [item.public_dict() for item in self.consumption_cards],
            "next_actions": list(self.next_actions),
            "source_schemas": list(self.source_schemas),
            "notes_used": self.notes_used,
            "execution_first": self.execution_first,
            "direct_consumption": self.direct_consumption,
            "shell_only": self.shell_only,
            "learning_loop_closed": self.learning_loop_closed,
            "blocks_only_activation_release": self.blocks_only_activation_release,
            "planner_hint_count": self.planner_hint_count,
            "skill_draft_count": self.skill_draft_count,
            "tool_candidate_count": self.tool_candidate_count,
            "consumption_card_count": self.consumption_card_count,
            "writes_memory": self.writes_memory,
            "writes_skill_registry": self.writes_skill_registry,
            "registers_skill": self.registers_skill,
            "activates_skill": self.activates_skill,
            "produces_tool": self.produces_tool,
            "writes_tool_code": self.writes_tool_code,
            "registers_tool": self.registers_tool,
            "releases_tool_handle": self.releases_tool_handle,
            "calls_tool": self.calls_tool,
            "modifies_code": self.modifies_code,
            "applies_change": self.applies_change,
            "touches_kernel": self.touches_kernel,
            "report_digest": self.report_digest,
        }

    def summary_text(self) -> str:
        return (
            "L6.28 经验 / Skill / Tool 执行合流："
            f"status={self.status}；hints={self.planner_hint_count}；"
            f"skill_routes={self.skill_draft_count}；tool_routes={self.tool_candidate_count}；"
            f"cards={self.consumption_card_count}；direct_consumption={self.direct_consumption}。{self.summary}"
        )

    def markdown_report(self) -> str:
        lines = [
            "# 临渊者 L6.28 经验 / Skill / Tool 执行合流报告",
            "",
            f"- schema: `{self.schema}`",
            f"- status: `{self.status}`",
            f"- execution_first: `{self.execution_first}`",
            f"- direct_consumption: `{self.direct_consumption}`",
            f"- shell_only: `{self.shell_only}`",
            f"- report_digest: `{self.report_digest}`",
            "",
            "## 摘要",
            "",
            self.summary,
            "",
            "## Planner 执行提示路由",
            "",
        ]
        if not self.planner_hint_routes:
            lines.append("暂无 Planner 执行提示路由。")
        for item in self.planner_hint_routes:
            lines.append(f"- `{item.route_ref}` {item.title}: {item.action_hint}")
        lines.extend(["", "## Skill 草案消费路由", ""])
        if not self.skill_draft_routes:
            lines.append("暂无 Skill 草案消费路由。")
        for item in self.skill_draft_routes:
            lines.append(f"- `{item.route_ref}` {item.skill_name}: {item.purpose}")
        lines.extend(["", "## Tool 候选消费路由", ""])
        if not self.tool_candidate_routes:
            lines.append("暂无 Tool 候选消费路由。")
        for item in self.tool_candidate_routes:
            lines.append(f"- `{item.route_ref}` {item.tool_name}: {item.next_step}")
        lines.extend(["", "## 下一轮执行卡片", ""])
        if not self.consumption_cards:
            lines.append("暂无执行卡片。")
        for item in self.consumption_cards:
            lines.append(f"- `{item.card_ref}` {item.title}: {item.immediate_next_action}")
        lines.extend(["", "## 下一步", ""])
        for item in self.next_actions:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("> L6.28 只把经验、Skill 草案、Tool 候选合流为 Planner 可消费对象；正式写入、注册、激活、发布仍被治理链拦在后面。")
        return "\n".join(lines)


class LearningConvergenceBridge:
    """Runtime 外壳层学习合流器。"""

    def __init__(self) -> None:
        self._last_report: LearningConvergenceReport | None = None

    @property
    def last_report(self) -> LearningConvergenceReport | None:
        return self._last_report

    def reset(self) -> None:
        self._last_report = None

    def converge(
        self,
        *,
        experience_report: dict[str, Any] | None = None,
        skill_queue_report: dict[str, Any] | None = None,
        tool_request_report: dict[str, Any] | None = None,
        exoskeleton_report: dict[str, Any] | None = None,
        notes: str = "",
        max_items: int = 18,
    ) -> LearningConvergenceReport:
        limit = max(1, min(int(max_items), 50))
        exp = experience_report or {}
        skill = skill_queue_report or {}
        tool = tool_request_report or {}
        exo = exoskeleton_report or {}

        source_refs = _build_source_refs(exp, skill, tool, exo)
        planner_hint_routes = _build_planner_hint_routes(exp, skill, exo, limit=limit)
        skill_draft_routes = _build_skill_draft_routes(exp, skill, planner_hint_routes, limit=limit)
        tool_candidate_routes = _build_tool_candidate_routes(exp, tool, exo, limit=limit)
        manual_note = _safe_text(notes, limit=520)
        if manual_note and not planner_hint_routes:
            planner_hint_routes.append(
                PlannerHintRoute(
                    route_ref=_ref("planner_route", "manual", manual_note),
                    source_ref="manual:l6_28_notes",
                    title="人工执行力合流提示",
                    trigger="用户显式要求执行力第一或学习合流时。",
                    action_hint=f"下一轮计划优先采用该执行偏置：{manual_note}",
                    priority="P0_execution",
                )
            )
        consumption_cards = _build_consumption_cards(planner_hint_routes, skill_draft_routes, tool_candidate_routes, limit=limit)
        status = "empty" if not (planner_hint_routes or skill_draft_routes or tool_candidate_routes or consumption_cards) else "learning_convergence_ready"
        next_actions = _next_actions(planner_hint_routes, skill_draft_routes, tool_candidate_routes, consumption_cards)
        source_schemas = _source_schemas(exp, skill, tool, exo)
        summary = _summary(
            hints=len(planner_hint_routes),
            skills=len(skill_draft_routes),
            tools=len(tool_candidate_routes),
            cards=len(consumption_cards),
            notes=notes,
        )
        report = LearningConvergenceReport(
            schema=LEARNING_CONVERGENCE_SCHEMA,
            generated_at=time(),
            status=status,
            summary=summary,
            source_refs=source_refs,
            planner_hint_routes=planner_hint_routes,
            skill_draft_routes=skill_draft_routes,
            tool_candidate_routes=tool_candidate_routes,
            consumption_cards=consumption_cards,
            next_actions=next_actions,
            source_schemas=source_schemas,
            notes_used=bool(manual_note),
        )
        report = LearningConvergenceReport(**{**report.__dict__, "report_digest": stable_learning_convergence_digest(report)})
        self._last_report = report
        return report

    def public_dict(self) -> dict[str, Any]:
        if self._last_report is None:
            return {"schema": LEARNING_CONVERGENCE_SCHEMA, "status": "empty", "message": "暂无 L6.28 学习合流报告，请先执行 /learning-converge-build。"}
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
        cards = "; ".join(item.immediate_next_action for item in report.consumption_cards[:3]) or "无"
        hints = ", ".join(item.title for item in report.planner_hint_routes[:3]) or "无"
        return (
            "最近 L6.28 学习合流："
            f"status={report.status}; cards={report.consumption_card_count}; hints={hints}; "
            f"next={cards}; direct_consumption=True; activation_release_gated=True"
        )[:1200]


def build_learning_convergence_adapter(convergence: LearningConvergenceBridge, experience: Any, skill_queue: Any, tool_requests: Any, exoskeleton: Any):
    def learning_convergence_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            report = convergence.converge(
                experience_report=experience.public_dict(),
                skill_queue_report=skill_queue.public_dict(),
                tool_request_report=tool_requests.public_dict(),
                exoskeleton_report=exoskeleton.public_dict(),
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
                max_items=int(invocation.arguments.get("max_items") or 18),
            )
        except (TypeError, ValueError) as exc:
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.FAILED,
                f"学习合流失败：{exc}",
                error_code="learning_convergence_failed",
            )
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=report.summary_text(),
            data=report.public_dict(),
        )

    return learning_convergence_adapter


def stable_learning_convergence_digest(report: LearningConvergenceReport) -> str:
    payload = report.public_dict()
    payload.pop("generated_at", None)
    payload.pop("report_digest", None)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _build_source_refs(*reports: dict[str, Any]) -> list[LearningSourceRef]:
    refs: list[LearningSourceRef] = []
    mapping = [
        ("experience", reports[0] if len(reports) > 0 else {}, ("skill_candidates", "tool_gap_candidates", "lessons"), ["planner_hint_routes", "skill_draft_routes", "tool_candidate_routes"]),
        ("skill_queue", reports[1] if len(reports) > 1 else {}, ("draft_versions", "review_queue"), ["skill_draft_routes"]),
        ("tool_request", reports[2] if len(reports) > 2 else {}, ("production_requests", "review_queue"), ["tool_candidate_routes"]),
        ("exoskeleton", reports[3] if len(reports) > 3 else {}, ("planner_hints", "tool_candidate_tickets"), ["planner_hint_routes", "tool_candidate_routes", "consumption_cards"]),
    ]
    for source_kind, report, fields, contributes_to in mapping:
        if not isinstance(report, dict):
            continue
        schema = _safe_text(report.get("schema"), limit=160)
        status = _safe_text(report.get("status"), limit=80) or "unknown"
        count = 0
        for field_name in fields:
            value = report.get(field_name)
            if isinstance(value, list):
                count += len(value)
        if schema or status != "unknown" or count:
            refs.append(
                LearningSourceRef(
                    source_ref=_ref("source", source_kind, schema, status, count),
                    source_schema=schema or "unknown",
                    source_kind=source_kind,
                    status=status,
                    item_count=count,
                    contributes_to=contributes_to,
                )
            )
    return refs


def _build_planner_hint_routes(experience: dict[str, Any], skill_queue: dict[str, Any], exoskeleton: dict[str, Any], *, limit: int) -> list[PlannerHintRoute]:
    routes: list[PlannerHintRoute] = []
    for raw in _as_dicts(exoskeleton.get("planner_hints")):
        source_ref = _safe_text(raw.get("hint_ref") or raw.get("source_ref"), limit=180) or _ref("planner_source", raw)
        title = _safe_text(raw.get("title"), limit=140) or "外骨骼执行提示"
        trigger = _safe_text(raw.get("trigger"), limit=420) or "遇到相似任务时。"
        action_hint = _safe_text(raw.get("action_hint"), limit=720) or "优先复用该执行提示。"
        routes.append(
            PlannerHintRoute(
                route_ref=_ref("planner_route", source_ref, title, action_hint),
                source_ref=source_ref,
                title=title,
                trigger=trigger,
                action_hint=action_hint,
                priority="P0_execution",
            )
        )
    if not routes:
        for raw in _skill_sources(experience, skill_queue)[:limit]:
            source_ref = _safe_text(raw.get("draft_ref") or raw.get("candidate_ref") or raw.get("source_candidate_ref"), limit=180) or _ref("skill_source", raw)
            title = _safe_text(raw.get("skill_name") or raw.get("title"), limit=140) or "Skill 草案执行提示"
            purpose = _safe_text(raw.get("purpose"), limit=720) or "复用 Skill 草案经验，减少重复分析。"
            trigger = _safe_text(raw.get("trigger_hint") or raw.get("next_use_condition"), limit=420) or "遇到同类任务或同类失败模式时。"
            routes.append(
                PlannerHintRoute(
                    route_ref=_ref("planner_route", source_ref, title, purpose),
                    source_ref=source_ref,
                    title=title,
                    trigger=trigger,
                    action_hint=f"命中条件后直接采用：{purpose}",
                )
            )
    return _dedupe_routes(routes)[:limit]


def _build_skill_draft_routes(experience: dict[str, Any], skill_queue: dict[str, Any], planner_routes: list[PlannerHintRoute], *, limit: int) -> list[SkillDraftRoute]:
    by_source: dict[str, str] = {route.source_ref: route.route_ref for route in planner_routes}
    out: list[SkillDraftRoute] = []
    for raw in _skill_sources(experience, skill_queue)[:limit]:
        source_ref = _safe_text(raw.get("draft_ref") or raw.get("candidate_ref") or raw.get("source_candidate_ref"), limit=180) or _ref("skill_source", raw)
        skill_name = _safe_text(raw.get("skill_name") or raw.get("title"), limit=140) or "未命名 Skill 草案"
        purpose = _safe_text(raw.get("purpose"), limit=720) or "把候选经验转成下次可复用执行方法。"
        condition = _safe_text(raw.get("trigger_hint") or raw.get("next_use_condition"), limit=420) or "遇到同类任务时。"
        planner_ref = by_source.get(source_ref) or _ref("planner_route", source_ref, skill_name, purpose)
        out.append(
            SkillDraftRoute(
                route_ref=_ref("skill_route", source_ref, skill_name, purpose),
                source_ref=source_ref,
                skill_name=skill_name,
                purpose=purpose,
                next_use_condition=condition,
                planner_hint_ref=planner_ref,
            )
        )
    return _dedupe_routes(out)[:limit]


def _build_tool_candidate_routes(experience: dict[str, Any], tool_request: dict[str, Any], exoskeleton: dict[str, Any], *, limit: int) -> list[ToolCandidateRoute]:
    out: list[ToolCandidateRoute] = []
    for raw in _tool_sources(experience, tool_request, exoskeleton)[:limit]:
        source_ref = _safe_text(raw.get("ticket_ref") or raw.get("request_ref") or raw.get("candidate_ref") or raw.get("source_candidate_ref"), limit=180) or _ref("tool_source", raw)
        name = _safe_text(raw.get("tool_name") or raw.get("tool_name_hint") or raw.get("tool_gap_name"), limit=120) or "minimal_runtime_helper"
        purpose = _safe_text(raw.get("purpose") or raw.get("capability_need"), limit=760) or "补齐当前任务缺失的最小工具能力。"
        smoke = _safe_text(raw.get("smoke_test"), limit=520) or _infer_smoke_test(name, purpose)
        out.append(
            ToolCandidateRoute(
                route_ref=_ref("tool_route", source_ref, name, purpose, smoke),
                source_ref=source_ref,
                tool_name=_normalize_tool_name(name),
                purpose=purpose,
                smoke_test=smoke,
            )
        )
    return _dedupe_routes(out)[:limit]


def _build_consumption_cards(
    planner_routes: list[PlannerHintRoute],
    skill_routes: list[SkillDraftRoute],
    tool_routes: list[ToolCandidateRoute],
    *,
    limit: int,
) -> list[ExecutionConsumptionCard]:
    cards: list[ExecutionConsumptionCard] = []
    for route in planner_routes[: max(1, min(6, limit))]:
        cards.append(
            ExecutionConsumptionCard(
                card_ref=_ref("consumption_card", route.route_ref, route.title),
                title=f"优先消费 PlannerHint：{route.title}",
                consumed_refs=[route.route_ref, route.source_ref],
                immediate_next_action=f"下一轮计划器上下文前置该提示：{route.action_hint}",
                expected_execution_gain="减少重复分析、重复询问和候选队列跳转。",
            )
        )
    for route in skill_routes[: max(1, min(4, limit))]:
        cards.append(
            ExecutionConsumptionCard(
                card_ref=_ref("consumption_card", route.route_ref, route.skill_name),
                title=f"把 Skill 草案当作方法提示：{route.skill_name}",
                consumed_refs=[route.route_ref, route.source_ref, route.planner_hint_ref],
                immediate_next_action=f"命中 `{route.next_use_condition}` 时按 `{route.skill_name}` 的目的执行：{route.purpose}",
                expected_execution_gain="把 Skill 草案提前变成行动偏置，但不注册、不激活。",
            )
        )
    for route in tool_routes[: max(1, min(4, limit))]:
        cards.append(
            ExecutionConsumptionCard(
                card_ref=_ref("consumption_card", route.route_ref, route.tool_name),
                title=f"推进最小工具草案：{route.tool_name}",
                consumed_refs=[route.route_ref, route.source_ref],
                immediate_next_action=f"进入隔离草案与 smoke：{route.smoke_test}",
                expected_execution_gain="把缺工具问题压缩成一次性草案验证，不再停在队列报告。",
            )
        )
    return _dedupe_routes(cards)[:limit]


def _skill_sources(experience: dict[str, Any], skill_queue: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in _as_dicts(skill_queue.get("draft_versions")):
        items.append({"kind": "skill_draft", **item})
    for item in _as_dicts(experience.get("skill_candidates")):
        items.append({"kind": "skill_candidate", **item})
    return _dedupe_dicts(items, keys=("draft_ref", "candidate_ref", "skill_name"))


def _tool_sources(experience: dict[str, Any], tool_request: dict[str, Any], exoskeleton: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in _as_dicts(exoskeleton.get("tool_candidate_tickets")):
        items.append({"kind": "tool_ticket", **item})
    for item in _as_dicts(tool_request.get("production_requests")):
        items.append({"kind": "tool_request", **item})
    for item in _as_dicts(experience.get("tool_gap_candidates")):
        items.append({"kind": "tool_gap", **item})
    return _dedupe_dicts(items, keys=("ticket_ref", "request_ref", "candidate_ref", "tool_name", "tool_name_hint", "tool_gap_name"))


def _next_actions(
    planner_routes: list[PlannerHintRoute],
    skill_routes: list[SkillDraftRoute],
    tool_routes: list[ToolCandidateRoute],
    cards: list[ExecutionConsumptionCard],
) -> list[str]:
    actions: list[str] = []
    if cards:
        actions.append("把 ExecutionConsumptionCard 前置注入下一轮 Planner 上下文，直接驱动任务续接。")
    if planner_routes:
        actions.append("PlannerHintRoute 直接消费；不要求先注册正式 Skill。")
    if skill_routes:
        actions.append("SkillDraftRoute 仅作为方法提示使用；正式 Skill 注册/激活仍需后续质量门与发布门。")
    if tool_routes:
        actions.append("ToolCandidateRoute 下一步进入最小工具草案与 smoke；本阶段不写工具代码、不释放句柄。")
    if not actions:
        actions.append("先执行 L6.20-L6.23 生成经验、Skill 草案、Tool 请求或外骨骼提示，再进行 L6.28 合流。")
    actions.append("保持执行力第一：A0-A4 草案/合流/提示默认续接，A5、密钥、越权、正式发布仍硬卡。")
    return actions


def _summary(*, hints: int, skills: int, tools: int, cards: int, notes: str) -> str:
    note_hint = "；已接收人工备注" if _safe_text(notes, limit=120) else ""
    if hints <= 0 and skills <= 0 and tools <= 0 and cards <= 0:
        return f"暂无可合流对象，建议先执行经验沉淀、Skill 入队、Tool 请求或外骨骼压缩{note_hint}。"
    return (
        "已把经验、Skill 草案、Tool 候选和外骨骼输出合流为下一轮可消费执行对象；"
        f"PlannerHintRoute={hints}；SkillDraftRoute={skills}；ToolCandidateRoute={tools}；"
        f"ExecutionConsumptionCard={cards}{note_hint}。"
        "沉淀结果不再停留在报告层，而是进入 Planner 上下文和最小草案验证路径。"
    )


def _source_schemas(*reports: dict[str, Any]) -> list[str]:
    schemas: list[str] = []
    for report in reports:
        if isinstance(report, dict):
            schema = _safe_text(report.get("schema"), limit=160)
            if schema and schema not in schemas:
                schemas.append(schema)
    return schemas


def _infer_smoke_test(name: str, purpose: str) -> str:
    lower = f"{name} {purpose}".lower()
    if "zip" in lower or "打包" in lower or "交付" in lower:
        return "create tiny workspace fixture -> build candidate bundle in sandbox -> verify zip/integrity and no secrets"
    if "pytest" in lower or "compileall" in lower or "测试" in lower:
        return "create passing/failing toy checks -> run candidate parser in sandbox -> verify structured summary"
    if "scan" in lower or "扫描" in lower or "索引" in lower:
        return "create small file tree -> run candidate scan -> verify deterministic findings and no writes"
    return "create minimal fixture -> call candidate contract -> assert structured result and no registry/kernel mutation"


def _normalize_tool_name(name: str) -> str:
    text = _safe_text(name, limit=120).lower()
    text = re.sub(r"[^a-z0-9_\u4e00-\u9fff]+", "_", text).strip("_")
    return text[:80] or "minimal_runtime_helper"


def _as_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _dedupe_dicts(items: list[dict[str, Any]], *, keys: tuple[str, ...]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        key = "|".join(_safe_text(item.get(name), limit=200) for name in keys)
        if not key.strip("|"):
            key = json.dumps(item, ensure_ascii=False, sort_keys=True)[:500]
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        out.append(item)
    return out


def _dedupe_routes(items: list[Any]) -> list[Any]:
    seen: set[str] = set()
    out: list[Any] = []
    for item in items:
        public = item.public_dict() if hasattr(item, "public_dict") else dict(item)
        ref = _safe_text(public.get("route_ref") or public.get("card_ref") or public.get("source_ref"), limit=240)
        key = ref or json.dumps(public, ensure_ascii=False, sort_keys=True)[:700]
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        out.append(item)
    return out


def _safe_text(value: Any, *, limit: int = 700) -> str:
    text = redact_text(str(value or ""))
    text = SENSITIVE_PATTERN.sub(lambda m: f"{m.group(1)}=<redacted>", text)
    for word in SENSITIVE_WORDS:
        text = re.sub(re.escape(word), f"{word[:2]}***", text, flags=re.IGNORECASE)
    return text.strip()[:limit]


def _ref(prefix: str, *parts: Any) -> str:
    material = "|".join(_safe_text(part, limit=500) for part in parts)
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}:l6_28_{digest}"
