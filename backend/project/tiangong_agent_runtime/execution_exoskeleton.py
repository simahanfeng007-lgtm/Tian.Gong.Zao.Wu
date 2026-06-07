"""L6.23 LLM 外骨骼执行力压缩层。

该模块不再继续堆叠 Skill/Tool 审阅层，而是把 L6.20-L6.22 的候选结果压缩成
LLM 下一轮执行可以直接消费的 PlannerHint 与最小 ToolCandidateTicket。

边界：
- A0-A4 草案/提示/票据生成默认放开，优先服务 LLM 执行力；
- 只卡真实发布、注册、激活、工具句柄释放和 A5 高危；
- 本模块不写正式 Skill 注册表、不生产真实 Tool、不调用新 Tool、不改 tiangong_kernel。
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

EXOSKELETON_SCHEMA = "tiangong.l6_23.execution_exoskeleton.v1"
SENSITIVE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer|token|secret|password|credential)\s*[:=]\s*[^\s,;]+"
)
SENSITIVE_WORDS = ("api_key", "apikey", "authorization", "bearer", "token", "secret", "password", "credential")


@dataclass(frozen=True)
class PlannerExecutionHint:
    """给 LLM / Planner 直接消费的执行提示。

    它不是正式 Skill，不进入 Skill 注册表。目标是减少 LLM 下次执行时的
    分析成本、绕路成本和重复询问成本。
    """

    hint_ref: str
    source_ref: str
    title: str
    trigger: str
    action_hint: str
    execution_bias: str = "do_next_without_extra_queue"
    confidence: float = 0.72
    source_kind: str = "skill_candidate"
    writes_skill_registry: bool = False
    activates_skill: bool = False
    applies_change: bool = False

    def __post_init__(self) -> None:
        if self.writes_skill_registry or self.activates_skill or self.applies_change:
            raise ValueError("L6.23 PlannerExecutionHint cannot write registry, activate skill or apply change")

    def public_dict(self) -> dict[str, Any]:
        return {
            "hint_ref": self.hint_ref,
            "source_ref": self.source_ref,
            "title": self.title,
            "trigger": self.trigger,
            "action_hint": self.action_hint,
            "execution_bias": self.execution_bias,
            "confidence": self.confidence,
            "source_kind": self.source_kind,
            "writes_skill_registry": self.writes_skill_registry,
            "activates_skill": self.activates_skill,
            "applies_change": self.applies_change,
        }


@dataclass(frozen=True)
class ToolCandidateTicket:
    """最小工具候选票据。

    这是 LLM 外骨骼模式下的短链对象：把“缺工具”压缩成一个可以立即进入
    沙箱草案/一次性 smoke 验证的最小规格，不再拆成多层队列。
    """

    ticket_ref: str
    source_ref: str
    tool_name: str
    purpose: str
    inputs: list[str] = field(default_factory=lambda: ["workspace_relative_path", "safe_text_or_json_arguments"])
    outputs: list[str] = field(default_factory=lambda: ["structured_json_result", "short_human_summary"])
    smoke_test: str = "build minimal fixture -> call candidate contract -> assert structured result and no side effects"
    rollback_note: str = "delete sandbox draft and discard ticket; no registry or kernel mutation occurred"
    risk_level: str = "A2_draft/A3_if_workspace_sandbox"
    execution_bias: str = "minimal_candidate_first"
    max_spec_fields: int = 7
    direct_to_sandbox: bool = True
    produces_tool: bool = False
    writes_tool_code: bool = False
    registers_tool: bool = False
    releases_tool_handle: bool = False
    calls_tool: bool = False
    touches_kernel: bool = False

    def __post_init__(self) -> None:
        forbidden = (
            self.produces_tool,
            self.writes_tool_code,
            self.registers_tool,
            self.releases_tool_handle,
            self.calls_tool,
            self.touches_kernel,
        )
        if any(forbidden):
            raise ValueError("L6.23 ToolCandidateTicket cannot produce/write/register/release/call/touch kernel")
        if self.max_spec_fields > 7:
            raise ValueError("L6.23 ToolCandidateTicket must remain minimal and cannot exceed 7 core spec fields")

    def public_dict(self) -> dict[str, Any]:
        return {
            "ticket_ref": self.ticket_ref,
            "source_ref": self.source_ref,
            "tool_name": self.tool_name,
            "purpose": self.purpose,
            "inputs": list(self.inputs),
            "outputs": list(self.outputs),
            "smoke_test": self.smoke_test,
            "rollback_note": self.rollback_note,
            "risk_level": self.risk_level,
            "execution_bias": self.execution_bias,
            "max_spec_fields": self.max_spec_fields,
            "direct_to_sandbox": self.direct_to_sandbox,
            "produces_tool": self.produces_tool,
            "writes_tool_code": self.writes_tool_code,
            "registers_tool": self.registers_tool,
            "releases_tool_handle": self.releases_tool_handle,
            "calls_tool": self.calls_tool,
            "touches_kernel": self.touches_kernel,
        }


@dataclass(frozen=True)
class ExecutionExoskeletonReport:
    schema: str
    generated_at: float
    status: str
    strategy: str
    summary: str
    planner_hints: list[PlannerExecutionHint] = field(default_factory=list)
    tool_candidate_tickets: list[ToolCandidateTicket] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    source_schemas: list[str] = field(default_factory=list)
    notes_used: bool = False
    execution_first: bool = True
    minimal_chain: bool = True
    draft_only: bool = True
    governance_blocks_only_activation: bool = True
    writes_skill_registry: bool = False
    activates_skill: bool = False
    produces_tool: bool = False
    writes_tool_code: bool = False
    registers_tool: bool = False
    releases_tool_handle: bool = False
    calls_tool: bool = False
    modifies_code: bool = False
    applies_change: bool = False
    touches_kernel: bool = False

    def __post_init__(self) -> None:
        if not (self.execution_first and self.minimal_chain and self.draft_only and self.governance_blocks_only_activation):
            raise ValueError("L6.23 exoskeleton report must remain execution-first, minimal, draft-only and activation-gated")
        forbidden = (
            self.writes_skill_registry,
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
            raise ValueError("L6.23 exoskeleton report cannot perform registry/tool/code/change/kernel side effects")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "status": self.status,
            "strategy": self.strategy,
            "summary": self.summary,
            "planner_hints": [item.public_dict() for item in self.planner_hints],
            "tool_candidate_tickets": [item.public_dict() for item in self.tool_candidate_tickets],
            "next_actions": list(self.next_actions),
            "source_schemas": list(self.source_schemas),
            "notes_used": self.notes_used,
            "execution_first": self.execution_first,
            "minimal_chain": self.minimal_chain,
            "draft_only": self.draft_only,
            "governance_blocks_only_activation": self.governance_blocks_only_activation,
            "writes_skill_registry": self.writes_skill_registry,
            "activates_skill": self.activates_skill,
            "produces_tool": self.produces_tool,
            "writes_tool_code": self.writes_tool_code,
            "registers_tool": self.registers_tool,
            "releases_tool_handle": self.releases_tool_handle,
            "calls_tool": self.calls_tool,
            "modifies_code": self.modifies_code,
            "applies_change": self.applies_change,
            "touches_kernel": self.touches_kernel,
        }

    def summary_text(self) -> str:
        return (
            "L6.23 LLM 外骨骼执行力压缩："
            f"status={self.status}；hints={len(self.planner_hints)}；"
            f"tool_tickets={len(self.tool_candidate_tickets)}；minimal_chain={self.minimal_chain}；"
            f"draft_only={self.draft_only}。{self.summary}"
        )

    def markdown_report(self) -> str:
        lines = [
            "# 临渊者 L6.23 LLM 外骨骼执行力压缩报告",
            "",
            f"- schema: `{self.schema}`",
            f"- status: `{self.status}`",
            f"- strategy: `{self.strategy}`",
            f"- execution_first: `{self.execution_first}`",
            f"- minimal_chain: `{self.minimal_chain}`",
            f"- draft_only: `{self.draft_only}`",
            "",
            "## 摘要",
            "",
            self.summary,
            "",
            "## Planner 执行提示",
            "",
        ]
        if not self.planner_hints:
            lines.append("暂无 Planner 执行提示。")
        for item in self.planner_hints:
            lines.append(f"- `{item.hint_ref}` {item.title}: {item.action_hint}")
        lines.extend(["", "## 最小 Tool 候选票据", ""])
        if not self.tool_candidate_tickets:
            lines.append("暂无 Tool 候选票据。")
        for item in self.tool_candidate_tickets:
            lines.append(f"- `{item.ticket_ref}` {item.tool_name}: {item.purpose}")
        lines.extend(["", "## 下一步", ""])
        for item in self.next_actions:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("> L6.23 只压缩为执行提示和最小候选票据；正式 Skill/Tool 激活仍由质量门、发布门、宿主与回滚证据控制。")
        return "\n".join(lines)


class ExecutionExoskeletonBridge:
    """Runtime 外壳层 LLM 外骨骼压缩器。"""

    def __init__(self) -> None:
        self._planner_hints: dict[str, PlannerExecutionHint] = {}
        self._tool_tickets: dict[str, ToolCandidateTicket] = {}
        self._last_report: ExecutionExoskeletonReport | None = None

    @property
    def last_report(self) -> ExecutionExoskeletonReport | None:
        return self._last_report

    def reset(self) -> None:
        self._planner_hints.clear()
        self._tool_tickets.clear()
        self._last_report = None

    def compress(
        self,
        *,
        experience_report: dict[str, Any] | None = None,
        skill_queue_report: dict[str, Any] | None = None,
        tool_request_report: dict[str, Any] | None = None,
        notes: str = "",
        max_items: int = 12,
    ) -> ExecutionExoskeletonReport:
        limit = max(1, min(int(max_items), 30))
        source_schemas = _source_schemas(experience_report, skill_queue_report, tool_request_report)
        hints_added = 0
        tickets_added = 0

        for draft in _skill_sources(experience_report, skill_queue_report)[:limit]:
            hint = _build_planner_hint(draft)
            if hint.hint_ref not in self._planner_hints:
                self._planner_hints[hint.hint_ref] = hint
                hints_added += 1

        for raw_tool in _tool_sources(experience_report, tool_request_report)[:limit]:
            ticket = _build_tool_ticket(raw_tool)
            if ticket.ticket_ref not in self._tool_tickets:
                self._tool_tickets[ticket.ticket_ref] = ticket
                tickets_added += 1

        manual_note = _safe_text(notes, limit=520)
        if manual_note and not self._planner_hints:
            hint = PlannerExecutionHint(
                hint_ref=_ref("planner_hint", "manual", manual_note),
                source_ref="manual:l6_23_notes",
                title="人工外骨骼执行提示",
                trigger="用户显式要求执行力优先或外骨骼压缩时。",
                action_hint=f"优先按用户备注执行：{manual_note}",
                source_kind="manual_notes",
            )
            self._planner_hints[hint.hint_ref] = hint
            hints_added += 1
        if manual_note and not self._tool_tickets and _mentions_tool_need(manual_note):
            ticket = ToolCandidateTicket(
                ticket_ref=_ref("tool_ticket", "manual", manual_note),
                source_ref="manual:l6_23_notes",
                tool_name=_normalize_tool_name("minimal_exoskeleton_helper"),
                purpose=manual_note,
                inputs=_infer_inputs(manual_note),
                outputs=_infer_outputs(manual_note),
                smoke_test=_infer_smoke_test("minimal_exoskeleton_helper", manual_note),
            )
            self._tool_tickets[ticket.ticket_ref] = ticket
            tickets_added += 1

        hints = list(self._planner_hints.values())
        tickets = list(self._tool_tickets.values())
        status = "empty" if not hints and not tickets else "exoskeleton_ready"
        if (hints or tickets) and hints_added == 0 and tickets_added == 0:
            status = "exoskeleton_ready_no_new"

        next_actions = _next_actions(hints, tickets)
        summary = _summary(
            hints=len(hints),
            tickets=len(tickets),
            hints_added=hints_added,
            tickets_added=tickets_added,
            notes=notes,
        )
        report = ExecutionExoskeletonReport(
            schema=EXOSKELETON_SCHEMA,
            generated_at=time(),
            status=status,
            strategy="llm_execution_exoskeleton",
            summary=summary,
            planner_hints=hints,
            tool_candidate_tickets=tickets,
            next_actions=next_actions,
            source_schemas=source_schemas,
            notes_used=bool(_safe_text(notes, limit=200)),
        )
        self._last_report = report
        return report

    def public_dict(self) -> dict[str, Any]:
        if self._last_report is None:
            if not self._planner_hints and not self._tool_tickets:
                return {"schema": EXOSKELETON_SCHEMA, "status": "empty", "message": "暂无 LLM 外骨骼压缩报告，请先执行 /exoskeleton-build。"}
            self._last_report = ExecutionExoskeletonReport(
                schema=EXOSKELETON_SCHEMA,
                generated_at=time(),
                status="exoskeleton_ready",
                strategy="llm_execution_exoskeleton",
                summary=f"已存在 {len(self._planner_hints)} 条 PlannerHint 与 {len(self._tool_tickets)} 个 ToolCandidateTicket。",
                planner_hints=list(self._planner_hints.values()),
                tool_candidate_tickets=list(self._tool_tickets.values()),
                next_actions=_next_actions(list(self._planner_hints.values()), list(self._tool_tickets.values())),
            )
        return self._last_report.public_dict()

    def export_json(self, path: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def build_planner_hint(self) -> str:
        if not self._planner_hints and not self._tool_tickets:
            return ""
        hint_titles = ", ".join(item.title for item in list(self._planner_hints.values())[:3]) or "无"
        ticket_names = ", ".join(item.tool_name for item in list(self._tool_tickets.values())[:3]) or "无"
        return (
            "最近 L6.23 LLM 外骨骼压缩："
            f"planner_hints={len(self._planner_hints)}; tool_tickets={len(self._tool_tickets)}; "
            f"hints={hint_titles}; tools={ticket_names}; "
            "strategy=execution_first/minimal_chain; quality_gate_blocks_only_activation=True"
        )


def build_execution_exoskeleton_adapter(exoskeleton: ExecutionExoskeletonBridge, experience: Any, skill_queue: Any, tool_requests: Any):
    def execution_exoskeleton_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            report = exoskeleton.compress(
                experience_report=experience.public_dict(),
                skill_queue_report=skill_queue.public_dict(),
                tool_request_report=tool_requests.public_dict(),
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
                max_items=int(invocation.arguments.get("max_items") or 12),
            )
        except (TypeError, ValueError) as exc:
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.FAILED,
                f"LLM 外骨骼压缩失败：{exc}",
                error_code="execution_exoskeleton_failed",
            )
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=report.summary_text(),
            data=report.public_dict(),
        )

    return execution_exoskeleton_adapter


def _skill_sources(experience: dict[str, Any] | None, skill_queue: dict[str, Any] | None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if isinstance(skill_queue, dict):
        for item in skill_queue.get("draft_versions", []) or []:
            if isinstance(item, dict):
                items.append({"kind": "skill_draft", **item})
    if isinstance(experience, dict):
        for item in experience.get("skill_candidates", []) or []:
            if isinstance(item, dict):
                items.append({"kind": "skill_candidate", **item})
    return _dedupe(items, key_names=("draft_ref", "candidate_ref", "skill_name"))


def _tool_sources(experience: dict[str, Any] | None, tool_requests: dict[str, Any] | None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if isinstance(tool_requests, dict):
        for item in tool_requests.get("production_requests", []) or []:
            if isinstance(item, dict):
                items.append({"kind": "tool_request", **item})
    if isinstance(experience, dict):
        for item in experience.get("tool_gap_candidates", []) or []:
            if isinstance(item, dict):
                items.append({"kind": "tool_gap", **item})
    return _dedupe(items, key_names=("request_ref", "candidate_ref", "tool_name_hint", "tool_gap_name"))


def _build_planner_hint(raw: dict[str, Any]) -> PlannerExecutionHint:
    source_ref = _safe_text(raw.get("draft_ref") or raw.get("candidate_ref") or raw.get("source_candidate_ref"), limit=160) or _ref("skill_source", raw)
    title = _safe_text(raw.get("skill_name") or raw.get("title"), limit=120) or "未命名执行提示"
    purpose = _safe_text(raw.get("purpose"), limit=520) or "复用已有候选经验，减少重复分析。"
    trigger = _safe_text(raw.get("trigger_hint"), limit=300) or "遇到相似任务、失败模式或重复操作时。"
    return PlannerExecutionHint(
        hint_ref=_ref("planner_hint", source_ref, title, purpose, trigger),
        source_ref=source_ref,
        title=title,
        trigger=trigger,
        action_hint=f"命中触发条件后优先采用：{purpose}",
        source_kind=_safe_text(raw.get("kind"), limit=80) or "skill_candidate",
    )


def _build_tool_ticket(raw: dict[str, Any]) -> ToolCandidateTicket:
    source_ref = _safe_text(raw.get("request_ref") or raw.get("candidate_ref") or raw.get("source_candidate_ref"), limit=160) or _ref("tool_source", raw)
    name = _safe_text(raw.get("tool_name_hint") or raw.get("tool_gap_name") or raw.get("tool_name"), limit=100) or "minimal_runtime_helper"
    purpose = _safe_text(raw.get("capability_need") or raw.get("purpose"), limit=620) or "补齐当前任务缺失的最小工具能力。"
    return ToolCandidateTicket(
        ticket_ref=_ref("tool_ticket", source_ref, name, purpose),
        source_ref=source_ref,
        tool_name=_normalize_tool_name(name),
        purpose=purpose,
        inputs=_infer_inputs(purpose),
        outputs=_infer_outputs(purpose),
        smoke_test=_infer_smoke_test(name, purpose),
    )


def _infer_inputs(purpose: str) -> list[str]:
    text = purpose.lower()
    if "zip" in text or "打包" in text or "发布" in text:
        return ["source_relative_path", "target_relative_zip_path", "manifest_metadata"]
    if "test" in text or "pytest" in text or "测试" in text:
        return ["workspace_relative_path", "test_target", "quality_command"]
    if "scan" in text or "扫描" in text or "检索" in text:
        return ["workspace_relative_path", "include_patterns", "max_files"]
    return ["workspace_relative_path", "safe_text_or_json_arguments"]


def _infer_outputs(purpose: str) -> list[str]:
    text = purpose.lower()
    if "报告" in text or "report" in text:
        return ["report_markdown", "structured_json_summary"]
    if "扫描" in text or "scan" in text:
        return ["finding_list", "structured_json_summary"]
    return ["structured_json_result", "short_human_summary"]


def _infer_smoke_test(name: str, purpose: str) -> str:
    lower = f"{name} {purpose}".lower()
    if "zip" in lower or "打包" in lower:
        return "create tiny workspace fixture -> build candidate bundle in sandbox -> verify zip exists and excludes secrets"
    if "pytest" in lower or "测试" in lower:
        return "create passing and failing toy tests -> run candidate in sandbox -> verify returncode and parsed summary"
    if "scan" in lower or "扫描" in lower:
        return "create small file tree -> run candidate scan -> verify deterministic finding list and no file writes"
    return "create minimal fixture -> call candidate contract -> assert structured result and no registry/kernel mutation"


def _next_actions(hints: list[PlannerExecutionHint], tickets: list[ToolCandidateTicket]) -> list[str]:
    actions: list[str] = []
    if hints:
        actions.append("把 PlannerExecutionHint 作为下一轮计划器上下文优先提示，减少重复分析和重复询问。")
    if tickets:
        actions.append("对最高优先级 ToolCandidateTicket 生成单文件最小草案与 smoke test，进入隔离沙箱一次性验证。")
    if hints or tickets:
        actions.append("质量门只卡正式注册、激活、发布；不阻断 A0-A4 草案生成和执行续接。")
    else:
        actions.append("先执行 /reflect 或 /tool-request-build 产生经验与工具缺口，再进行外骨骼压缩。")
    return actions


def _summary(*, hints: int, tickets: int, hints_added: int, tickets_added: int, notes: str) -> str:
    note_hint = "；已接收人工备注" if _safe_text(notes, limit=120) else ""
    if hints <= 0 and tickets <= 0:
        return f"暂无可压缩候选。建议先生成经验候选或工具缺口{note_hint}。"
    return (
        "已将 Skill/Tool 候选压缩为 LLM 可直接消费的执行外骨骼；"
        f"PlannerHint={hints}（本次新增 {hints_added}）；"
        f"ToolCandidateTicket={tickets}（本次新增 {tickets_added}）{note_hint}。"
        "后续不再增加重型审阅层，优先进入最小草案与一次性验证。"
    )


def _mentions_tool_need(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in ("tool", "工具", "票据", "候选", "草案", "sandbox", "沙箱", "helper"))


def _source_schemas(*reports: dict[str, Any] | None) -> list[str]:
    schemas: list[str] = []
    for report in reports:
        if isinstance(report, dict):
            schema = _safe_text(report.get("schema"), limit=160)
            if schema and schema not in schemas:
                schemas.append(schema)
    return schemas


def _dedupe(items: list[dict[str, Any]], *, key_names: tuple[str, ...]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        key = "|".join(_safe_text(item.get(name), limit=200) for name in key_names)
        if not key.strip("|"):
            key = json.dumps(item, ensure_ascii=False, sort_keys=True)[:500]
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        out.append(item)
    return out


def _normalize_tool_name(name: str) -> str:
    text = _safe_text(name, limit=100).lower()
    text = re.sub(r"[^a-z0-9_\u4e00-\u9fff]+", "_", text).strip("_")
    if not text:
        return "minimal_runtime_helper"
    return text[:80]


def _safe_text(value: Any, *, limit: int = 700) -> str:
    text = redact_text(str(value or ""))
    text = SENSITIVE_PATTERN.sub(lambda m: f"{m.group(1)}=<redacted>", text)
    for word in SENSITIVE_WORDS:
        text = re.sub(re.escape(word), f"{word[:2]}***", text, flags=re.IGNORECASE)
    return text.strip()[:limit]


def _ref(prefix: str, *parts: Any) -> str:
    material = "|".join(_safe_text(part, limit=500) for part in parts)
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}:l6_23_{digest}"
