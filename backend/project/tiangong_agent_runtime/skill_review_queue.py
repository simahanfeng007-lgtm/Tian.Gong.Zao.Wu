"""L6.21 Skill 候选版本化与审阅队列。

该模块只把 L6.20 经验沉淀产生的 SkillCandidate 转成 Runtime 外壳层
草案版本与审阅队列。它面向 LLM 执行力优先：候选入队、草案版本化、
审阅队列生成默认放开；但不写正式 Skill 注册表、不激活真实 Skill、
不释放能力可见性、不绕过 L5 插件宿主与 L4 工具/模型治理链。
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

SKILL_QUEUE_SCHEMA = "tiangong.l6_21.skill_review_queue.v1"
SENSITIVE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer|token|secret|password|credential)\s*[:=]\s*[^\s,;]+"
)
SENSITIVE_WORDS = ("api_key", "apikey", "authorization", "bearer", "token", "secret", "password", "credential")


@dataclass(frozen=True)
class SkillDraftVersion:
    """Skill 草案版本。

    这是“候选 Skill 的版本化外壳”，不是正式 SkillVersion。正式注册、可见能力
    和工具句柄释放仍必须由后续治理链完成。
    """

    draft_ref: str
    source_candidate_ref: str
    source_lesson_refs: list[str]
    skill_name: str
    purpose: str
    trigger_hint: str
    version: str = "0.1.0-draft"
    status: str = "draft_ready"
    execution_priority: str = "execution_first"
    validation_refs: list[str] = field(default_factory=list)
    rollback_refs: list[str] = field(default_factory=list)
    review_required: bool = True
    activation_allowed: bool = False
    registers_skill: bool = False
    writes_skill_registry: bool = False
    visible_capability: bool = False

    def __post_init__(self) -> None:
        if self.activation_allowed or self.registers_skill or self.writes_skill_registry or self.visible_capability:
            raise ValueError("L6.21 SkillDraftVersion cannot activate, register, write or expose a real Skill")

    def public_dict(self) -> dict[str, Any]:
        return {
            "draft_ref": self.draft_ref,
            "source_candidate_ref": self.source_candidate_ref,
            "source_lesson_refs": list(self.source_lesson_refs),
            "skill_name": self.skill_name,
            "purpose": self.purpose,
            "trigger_hint": self.trigger_hint,
            "version": self.version,
            "status": self.status,
            "execution_priority": self.execution_priority,
            "validation_refs": list(self.validation_refs),
            "rollback_refs": list(self.rollback_refs),
            "review_required": self.review_required,
            "activation_allowed": self.activation_allowed,
            "registers_skill": self.registers_skill,
            "writes_skill_registry": self.writes_skill_registry,
            "visible_capability": self.visible_capability,
        }


@dataclass(frozen=True)
class SkillReviewQueueItem:
    """审阅队列项。

    队列项允许后续审阅、排序、转交，但不代表通过、不代表安装、不代表激活。
    """

    review_ref: str
    draft_ref: str
    source_candidate_ref: str
    status: str = "pending_review"
    priority: str = "P1_execution"
    review_policy: str = "A0-A4 candidate flow default allow; activation requires quality gate and rollback evidence"
    reviewer_chain: list[str] = field(default_factory=lambda: ["L6.18 quality_gate", "L6.19 release_gate", "L5 plugin_host", "L4 grounding"])
    quality_gate_required: str = "L6.18+L6.19 before real activation"
    applies_change: bool = False
    activates_skill: bool = False
    writes_skill_registry: bool = False

    def __post_init__(self) -> None:
        if self.applies_change or self.activates_skill or self.writes_skill_registry:
            raise ValueError("L6.21 SkillReviewQueueItem cannot apply change, activate Skill or write registry")

    def public_dict(self) -> dict[str, Any]:
        return {
            "review_ref": self.review_ref,
            "draft_ref": self.draft_ref,
            "source_candidate_ref": self.source_candidate_ref,
            "status": self.status,
            "priority": self.priority,
            "review_policy": self.review_policy,
            "reviewer_chain": list(self.reviewer_chain),
            "quality_gate_required": self.quality_gate_required,
            "applies_change": self.applies_change,
            "activates_skill": self.activates_skill,
            "writes_skill_registry": self.writes_skill_registry,
        }


@dataclass(frozen=True)
class SkillReviewQueueReport:
    schema: str
    generated_at: float
    status: str
    summary: str
    draft_versions: list[SkillDraftVersion] = field(default_factory=list)
    review_queue: list[SkillReviewQueueItem] = field(default_factory=list)
    source_report_schema: str = ""
    source_report_status: str = ""
    notes_used: bool = False
    queue_only: bool = True
    execution_first: bool = True
    writes_skill_registry: bool = False
    activates_skill: bool = False
    produces_tool: bool = False
    releases_tool_handle: bool = False
    modifies_code: bool = False
    applies_change: bool = False

    def __post_init__(self) -> None:
        if not self.queue_only or not self.execution_first:
            raise ValueError("L6.21 skill review queue must remain queue-only and execution-first")
        forbidden = (
            self.writes_skill_registry,
            self.activates_skill,
            self.produces_tool,
            self.releases_tool_handle,
            self.modifies_code,
            self.applies_change,
        )
        if any(forbidden):
            raise ValueError("L6.21 skill review queue cannot perform registry/tool/code/change side effects")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "status": self.status,
            "summary": self.summary,
            "draft_versions": [item.public_dict() for item in self.draft_versions],
            "review_queue": [item.public_dict() for item in self.review_queue],
            "source_report_schema": self.source_report_schema,
            "source_report_status": self.source_report_status,
            "notes_used": self.notes_used,
            "queue_only": self.queue_only,
            "execution_first": self.execution_first,
            "writes_skill_registry": self.writes_skill_registry,
            "activates_skill": self.activates_skill,
            "produces_tool": self.produces_tool,
            "releases_tool_handle": self.releases_tool_handle,
            "modifies_code": self.modifies_code,
            "applies_change": self.applies_change,
        }

    def summary_text(self) -> str:
        return (
            "L6.21 Skill 候选版本化审阅队列："
            f"status={self.status}；draft_versions={len(self.draft_versions)}；"
            f"review_queue={len(self.review_queue)}；queue_only={self.queue_only}；"
            f"execution_first={self.execution_first}。{self.summary}"
        )

    def markdown_report(self) -> str:
        lines = [
            "# 临渊者 L6.21 Skill 候选版本化与审阅队列报告",
            "",
            f"- schema: `{self.schema}`",
            f"- status: `{self.status}`",
            f"- queue_only: `{self.queue_only}`",
            f"- execution_first: `{self.execution_first}`",
            f"- writes_skill_registry: `{self.writes_skill_registry}`",
            f"- activates_skill: `{self.activates_skill}`",
            f"- applies_change: `{self.applies_change}`",
            "",
            "## 摘要",
            "",
            self.summary,
            "",
            "## Skill 草案版本",
            "",
        ]
        if not self.draft_versions:
            lines.append("暂无 Skill 草案版本。")
        for item in self.draft_versions:
            lines.append(f"- `{item.draft_ref}` {item.skill_name} / {item.version}: {item.purpose}")
        lines.extend(["", "## 审阅队列", ""])
        if not self.review_queue:
            lines.append("暂无审阅队列项。")
        for item in self.review_queue:
            lines.append(f"- `{item.review_ref}` -> `{item.draft_ref}` [{item.priority}] {item.review_policy}")
        lines.append("")
        lines.append("> L6.21 只做候选版本化和审阅入队；正式激活必须经质量门、发布门、回滚证据和宿主治理。")
        return "\n".join(lines)


class SkillReviewQueueBridge:
    """Runtime 外壳层 Skill 草案版本与审阅队列。"""

    def __init__(self) -> None:
        self._drafts: dict[str, SkillDraftVersion] = {}
        self._queue: dict[str, SkillReviewQueueItem] = {}
        self._last_report: SkillReviewQueueReport | None = None

    @property
    def last_report(self) -> SkillReviewQueueReport | None:
        return self._last_report

    def reset(self) -> None:
        self._drafts.clear()
        self._queue.clear()
        self._last_report = None

    def queue_from_experience(
        self,
        *,
        experience_report: dict[str, Any] | None = None,
        notes: str = "",
        max_items: int = 20,
    ) -> SkillReviewQueueReport:
        source = experience_report or {}
        candidates = source.get("skill_candidates", []) if isinstance(source, dict) else []
        limit = max(1, min(int(max_items), 100))
        added = 0
        for candidate in candidates[:limit]:
            if not isinstance(candidate, dict):
                continue
            draft = _build_draft(candidate)
            if draft.draft_ref not in self._drafts:
                self._drafts[draft.draft_ref] = draft
                added += 1
            queue_item = _build_queue_item(draft)
            if queue_item.review_ref not in self._queue:
                self._queue[queue_item.review_ref] = queue_item

        draft_versions = list(self._drafts.values())
        review_queue = list(self._queue.values())
        source_status = _safe_text(source.get("status", ""), limit=80) if isinstance(source, dict) else ""
        status = "empty" if not draft_versions else "queue_ready"
        if candidates and added == 0 and draft_versions:
            status = "queue_ready_no_new"
        summary = _build_summary(
            source_status=source_status,
            source_count=len(candidates) if isinstance(candidates, list) else 0,
            added=added,
            total=len(draft_versions),
            notes=notes,
        )
        report = SkillReviewQueueReport(
            schema=SKILL_QUEUE_SCHEMA,
            generated_at=time(),
            status=status,
            summary=summary,
            draft_versions=draft_versions,
            review_queue=review_queue,
            source_report_schema=_safe_text(source.get("schema", ""), limit=120) if isinstance(source, dict) else "",
            source_report_status=source_status,
            notes_used=bool(_safe_text(notes, limit=200)),
        )
        self._last_report = report
        return report

    def public_dict(self) -> dict[str, Any]:
        if self._last_report is None:
            if not self._drafts:
                return {"schema": SKILL_QUEUE_SCHEMA, "status": "empty", "message": "暂无 Skill 草案版本队列，请先执行 /skill-queue-build。"}
            self._last_report = SkillReviewQueueReport(
                schema=SKILL_QUEUE_SCHEMA,
                generated_at=time(),
                status="queue_ready",
                summary=f"已存在 {len(self._drafts)} 个 Skill 草案版本与 {len(self._queue)} 个审阅队列项。",
                draft_versions=list(self._drafts.values()),
                review_queue=list(self._queue.values()),
            )
        return self._last_report.public_dict()

    def export_json(self, path: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def build_planner_hint(self) -> str:
        if not self._drafts:
            return ""
        names = ", ".join(item.skill_name for item in list(self._drafts.values())[:3]) or "无"
        return f"最近 L6.21 Skill 审阅队列：drafts={len(self._drafts)}; queued={len(self._queue)}; skills={names}; queue_only=True; execution_first=True"


def build_queue_skill_candidates_adapter(skill_queue: SkillReviewQueueBridge, experience: Any):
    def queue_skill_candidates_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            report = skill_queue.queue_from_experience(
                experience_report=experience.public_dict(),
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
                max_items=int(invocation.arguments.get("max_items") or 20),
            )
        except (TypeError, ValueError) as exc:
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.FAILED,
                f"Skill 候选版本化入队失败：{exc}",
                error_code="skill_queue_failed",
            )
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=report.summary_text(),
            data=report.public_dict(),
        )

    return queue_skill_candidates_adapter


def _build_draft(candidate: dict[str, Any]) -> SkillDraftVersion:
    candidate_ref = _safe_text(candidate.get("candidate_ref"), limit=160) or _ref("skill_candidate", candidate)
    skill_name = _safe_text(candidate.get("skill_name"), limit=120) or "未命名 Skill 候选"
    purpose = _safe_text(candidate.get("purpose"), limit=700) or "待补充用途说明。"
    trigger_hint = _safe_text(candidate.get("trigger_hint"), limit=360) or "由 L6.20 经验沉淀触发。"
    source_lesson_refs = [_safe_text(item, limit=160) for item in _as_list(candidate.get("source_lesson_refs"))[:20]]
    validation_refs = [_safe_text(item, limit=160) for item in _as_list(candidate.get("validation_refs"))[:20]]
    rollback_refs = [_safe_text(item, limit=160) for item in _as_list(candidate.get("rollback_refs"))[:20]]
    return SkillDraftVersion(
        draft_ref=_ref("skill_draft", candidate_ref, skill_name, purpose, trigger_hint),
        source_candidate_ref=candidate_ref,
        source_lesson_refs=source_lesson_refs,
        skill_name=skill_name,
        purpose=purpose,
        trigger_hint=trigger_hint,
        validation_refs=validation_refs,
        rollback_refs=rollback_refs,
    )


def _build_queue_item(draft: SkillDraftVersion) -> SkillReviewQueueItem:
    return SkillReviewQueueItem(
        review_ref=_ref("skill_review", draft.draft_ref, draft.source_candidate_ref),
        draft_ref=draft.draft_ref,
        source_candidate_ref=draft.source_candidate_ref,
    )


def _build_summary(*, source_status: str, source_count: int, added: int, total: int, notes: str) -> str:
    note_hint = "；已接收人工备注" if _safe_text(notes, limit=120) else ""
    if total <= 0:
        return f"未发现可版本化的 Skill 候选。source_status={source_status or 'empty'}；source_candidates={source_count}{note_hint}。"
    return (
        "Skill 候选已转成草案版本并进入审阅队列；"
        f"source_status={source_status or 'unknown'}；source_candidates={source_count}；"
        f"本次新增={added}；队列累计={total}{note_hint}。"
        "草案可继续排序、审阅、导出和转交，但不会自动注册或激活。"
    )


def _safe_text(value: Any, *, limit: int = 700) -> str:
    text = redact_text(str(value or ""))
    text = SENSITIVE_PATTERN.sub(lambda m: f"{m.group(1)}=<redacted>", text)
    for word in SENSITIVE_WORDS:
        text = re.sub(re.escape(word), f"{word[:2]}***", text, flags=re.IGNORECASE)
    return text.strip()[:limit]


def _ref(prefix: str, *parts: Any) -> str:
    material = "|".join(_safe_text(part, limit=500) for part in parts)
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}:l6_21_{digest}"


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value in (None, ""):
        return []
    return [value]
