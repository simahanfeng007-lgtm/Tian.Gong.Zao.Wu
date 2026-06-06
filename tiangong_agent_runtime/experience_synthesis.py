"""L6.20 经验沉淀与 Skill / Tool 候选转化桥。

该桥只在 Runtime 外壳层保存安全摘要，把近期执行上下文、工程诊断、质量门、
交付 Manifest 和人工备注转化为候选对象。它不写 Skill 注册表、不生产 Tool、
不修改源码、不释放工具句柄、不应用自迭代变更；后续必须交给 L3/L4/L5/L6
治理链继续验证、发布和回滚。
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

EXPERIENCE_SCHEMA = "tiangong.l6_20.experience_synthesis.v1"
SENSITIVE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer|token|secret|password|credential)\s*[:=]\s*[^\s,;]+"
)
SENSITIVE_WORDS = ("api_key", "apikey", "authorization", "bearer", "token", "secret", "password", "credential")


def _safe_text(value: Any, *, limit: int = 700) -> str:
    text = redact_text(str(value or ""))
    text = SENSITIVE_PATTERN.sub(lambda m: f"{m.group(1)}=<redacted>", text)
    for word in SENSITIVE_WORDS:
        text = re.sub(re.escape(word), f"{word[:2]}***", text, flags=re.IGNORECASE)
    return text.strip()[:limit]


def _candidate_ref(prefix: str, *parts: Any) -> str:
    material = "|".join(_safe_text(part, limit=300) for part in parts)
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}:l6_20_{digest}"


@dataclass(frozen=True)
class ExperienceSignal:
    signal_ref: str
    source: str
    kind: str
    summary: str
    evidence_refs: list[str] = field(default_factory=list)
    severity: str = "P3"
    confidence: float = 0.70

    def public_dict(self) -> dict[str, Any]:
        return {
            "signal_ref": self.signal_ref,
            "source": self.source,
            "kind": self.kind,
            "summary": self.summary,
            "evidence_refs": list(self.evidence_refs),
            "severity": self.severity,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class LessonCandidate:
    lesson_ref: str
    source_signal_refs: list[str]
    lesson_type: str
    summary: str
    reusable_condition: str
    anti_pattern: str = ""
    confidence: float = 0.72
    not_written_to_memory: bool = True

    def public_dict(self) -> dict[str, Any]:
        return {
            "lesson_ref": self.lesson_ref,
            "source_signal_refs": list(self.source_signal_refs),
            "lesson_type": self.lesson_type,
            "summary": self.summary,
            "reusable_condition": self.reusable_condition,
            "anti_pattern": self.anti_pattern,
            "confidence": self.confidence,
            "not_written_to_memory": self.not_written_to_memory,
        }


@dataclass(frozen=True)
class SkillCandidate:
    candidate_ref: str
    source_lesson_refs: list[str]
    skill_name: str
    purpose: str
    trigger_hint: str
    validation_refs: list[str] = field(default_factory=list)
    rollback_refs: list[str] = field(default_factory=list)
    registers_skill: bool = False
    writes_skill: bool = False
    visible_capability: bool = False

    def __post_init__(self) -> None:
        if self.registers_skill or self.writes_skill or self.visible_capability:
            raise ValueError("L6.20 SkillCandidate cannot register, write or expose a real Skill")

    def public_dict(self) -> dict[str, Any]:
        return {
            "candidate_ref": self.candidate_ref,
            "source_lesson_refs": list(self.source_lesson_refs),
            "skill_name": self.skill_name,
            "purpose": self.purpose,
            "trigger_hint": self.trigger_hint,
            "validation_refs": list(self.validation_refs),
            "rollback_refs": list(self.rollback_refs),
            "registers_skill": self.registers_skill,
            "writes_skill": self.writes_skill,
            "visible_capability": self.visible_capability,
        }


@dataclass(frozen=True)
class ToolGapCandidate:
    candidate_ref: str
    source_lesson_refs: list[str]
    tool_gap_name: str
    capability_need: str
    governance_requirement: str
    validation_refs: list[str] = field(default_factory=list)
    produces_tool: bool = False
    releases_tool_handle: bool = False
    calls_tool: bool = False

    def __post_init__(self) -> None:
        if self.produces_tool or self.releases_tool_handle or self.calls_tool:
            raise ValueError("L6.20 ToolGapCandidate cannot produce, release or call tools")

    def public_dict(self) -> dict[str, Any]:
        return {
            "candidate_ref": self.candidate_ref,
            "source_lesson_refs": list(self.source_lesson_refs),
            "tool_gap_name": self.tool_gap_name,
            "capability_need": self.capability_need,
            "governance_requirement": self.governance_requirement,
            "validation_refs": list(self.validation_refs),
            "produces_tool": self.produces_tool,
            "releases_tool_handle": self.releases_tool_handle,
            "calls_tool": self.calls_tool,
        }


@dataclass(frozen=True)
class GovernanceTransferItem:
    transfer_ref: str
    target_chain: str
    source_candidate_refs: list[str]
    required_gate: str
    summary: str
    applies_change: bool = False
    auto_evolution_allowed: bool = False

    def __post_init__(self) -> None:
        if self.applies_change or self.auto_evolution_allowed:
            raise ValueError("L6.20 GovernanceTransferItem cannot apply change or allow auto evolution")

    def public_dict(self) -> dict[str, Any]:
        return {
            "transfer_ref": self.transfer_ref,
            "target_chain": self.target_chain,
            "source_candidate_refs": list(self.source_candidate_refs),
            "required_gate": self.required_gate,
            "summary": self.summary,
            "applies_change": self.applies_change,
            "auto_evolution_allowed": self.auto_evolution_allowed,
        }


@dataclass(frozen=True)
class ExperienceSynthesisReport:
    schema: str
    generated_at: float
    status: str
    summary: str
    signals: list[ExperienceSignal] = field(default_factory=list)
    lessons: list[LessonCandidate] = field(default_factory=list)
    skill_candidates: list[SkillCandidate] = field(default_factory=list)
    tool_gap_candidates: list[ToolGapCandidate] = field(default_factory=list)
    governance_transfers: list[GovernanceTransferItem] = field(default_factory=list)
    manual_notes_used: bool = False
    candidate_only: bool = True
    writes_skill_registry: bool = False
    writes_memory: bool = False
    produces_tool: bool = False
    releases_tool_handle: bool = False
    modifies_code: bool = False
    applies_change: bool = False

    def __post_init__(self) -> None:
        if not self.candidate_only:
            raise ValueError("L6.20 experience synthesis must remain candidate-only")
        forbidden = (
            self.writes_skill_registry,
            self.writes_memory,
            self.produces_tool,
            self.releases_tool_handle,
            self.modifies_code,
            self.applies_change,
        )
        if any(forbidden):
            raise ValueError("L6.20 experience synthesis cannot perform write/production/change side effects")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "status": self.status,
            "summary": self.summary,
            "signals": [item.public_dict() for item in self.signals],
            "lessons": [item.public_dict() for item in self.lessons],
            "skill_candidates": [item.public_dict() for item in self.skill_candidates],
            "tool_gap_candidates": [item.public_dict() for item in self.tool_gap_candidates],
            "governance_transfers": [item.public_dict() for item in self.governance_transfers],
            "manual_notes_used": self.manual_notes_used,
            "candidate_only": self.candidate_only,
            "writes_skill_registry": self.writes_skill_registry,
            "writes_memory": self.writes_memory,
            "produces_tool": self.produces_tool,
            "releases_tool_handle": self.releases_tool_handle,
            "modifies_code": self.modifies_code,
            "applies_change": self.applies_change,
        }

    def summary_text(self) -> str:
        return (
            "L6.20 经验沉淀候选报告："
            f"status={self.status}；signals={len(self.signals)}；lessons={len(self.lessons)}；"
            f"skill_candidates={len(self.skill_candidates)}；tool_gap_candidates={len(self.tool_gap_candidates)}；"
            f"governance_transfers={len(self.governance_transfers)}。{self.summary}"
        )

    def markdown_report(self) -> str:
        lines = [
            "# 临渊者 L6.20 经验沉淀与候选转化报告",
            "",
            f"- schema: `{self.schema}`",
            f"- status: `{self.status}`",
            f"- candidate_only: `{self.candidate_only}`",
            f"- writes_skill_registry: `{self.writes_skill_registry}`",
            f"- produces_tool: `{self.produces_tool}`",
            f"- applies_change: `{self.applies_change}`",
            "",
            "## 摘要",
            "",
            self.summary,
            "",
            "## 经验信号",
            "",
        ]
        if not self.signals:
            lines.append("暂无经验信号。")
        for item in self.signals:
            lines.append(f"- `{item.signal_ref}` [{item.severity}] {item.kind}: {item.summary}")
        lines.extend(["", "## 可复用教训", ""])
        if not self.lessons:
            lines.append("暂无可复用教训候选。")
        for item in self.lessons:
            lines.append(f"- `{item.lesson_ref}` {item.lesson_type}: {item.summary}")
        lines.extend(["", "## Skill 候选", ""])
        if not self.skill_candidates:
            lines.append("暂无 Skill 候选。")
        for item in self.skill_candidates:
            lines.append(f"- `{item.candidate_ref}` {item.skill_name}: {item.purpose}")
        lines.extend(["", "## Tool 缺口候选", ""])
        if not self.tool_gap_candidates:
            lines.append("暂无 Tool 缺口候选。")
        for item in self.tool_gap_candidates:
            lines.append(f"- `{item.candidate_ref}` {item.tool_gap_name}: {item.capability_need}")
        lines.extend(["", "## 治理转交", ""])
        if not self.governance_transfers:
            lines.append("暂无治理转交项。")
        for item in self.governance_transfers:
            lines.append(f"- `{item.transfer_ref}` -> {item.target_chain} / {item.required_gate}: {item.summary}")
        lines.append("")
        lines.append("> 本报告只包含安全摘要与候选引用，不包含完整 prompt、API Key、完整源码或敏感凭据。")
        return "\n".join(lines)


class ExperienceSynthesisBridge:
    """保存最近一次 L6.20 经验沉淀候选报告。"""

    def __init__(self) -> None:
        self._last_report: ExperienceSynthesisReport | None = None

    @property
    def last_report(self) -> ExperienceSynthesisReport | None:
        return self._last_report

    def reset(self) -> None:
        self._last_report = None

    def synthesize(
        self,
        *,
        context_snapshot: dict[str, Any] | None = None,
        diagnosis: dict[str, Any] | None = None,
        quality_gate: dict[str, Any] | None = None,
        delivery: dict[str, Any] | None = None,
        manual_notes: str = "",
        max_candidates: int = 12,
    ) -> ExperienceSynthesisReport:
        signals = _collect_signals(
            context_snapshot=context_snapshot or {},
            diagnosis=diagnosis or {},
            quality_gate=quality_gate or {},
            delivery=delivery or {},
            manual_notes=manual_notes,
        )[: max(1, min(int(max_candidates), 50))]
        lessons = _build_lessons(signals)
        skill_candidates = _build_skill_candidates(lessons)
        tool_gap_candidates = _build_tool_gap_candidates(lessons)
        governance_transfers = _build_governance_transfers(skill_candidates, tool_gap_candidates, lessons)
        status = "empty" if not signals else "candidate_ready"
        summary = _build_summary(signals, lessons, skill_candidates, tool_gap_candidates)
        report = ExperienceSynthesisReport(
            schema=EXPERIENCE_SCHEMA,
            generated_at=time(),
            status=status,
            summary=summary,
            signals=signals,
            lessons=lessons,
            skill_candidates=skill_candidates,
            tool_gap_candidates=tool_gap_candidates,
            governance_transfers=governance_transfers,
            manual_notes_used=bool(_safe_text(manual_notes, limit=200)),
        )
        self._last_report = report
        return report

    def public_dict(self) -> dict[str, Any]:
        if self._last_report is None:
            return {"schema": EXPERIENCE_SCHEMA, "status": "empty", "message": "暂无经验沉淀报告，请先执行 /reflect 或 synthesize_experience_candidates。"}
        return self._last_report.public_dict()

    def export_json(self, path: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def build_planner_hint(self) -> str:
        if self._last_report is None:
            return ""
        report = self._last_report
        skills = ", ".join(item.skill_name for item in report.skill_candidates[:3]) or "无"
        tools = ", ".join(item.tool_gap_name for item in report.tool_gap_candidates[:3]) or "无"
        return f"最近 L6.20 经验沉淀：status={report.status}; skill_candidates={skills}; tool_gap_candidates={tools}; candidate_only=True"


def build_synthesize_experience_adapter(
    experience_bridge: ExperienceSynthesisBridge,
    context_memory: Any,
    diagnostics: Any,
    quality_gate: Any,
    delivery: Any,
):
    def synthesize_experience_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            report = experience_bridge.synthesize(
                context_snapshot=context_memory.snapshot().public_dict(),
                diagnosis=diagnostics.public_dict(),
                quality_gate=quality_gate.public_dict(),
                delivery=delivery.public_dict(),
                manual_notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
                max_candidates=int(invocation.arguments.get("max_candidates") or 12),
            )
        except (TypeError, ValueError) as exc:
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"经验沉淀失败：{exc}", error_code="experience_synthesis_failed")
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=report.summary_text(),
            data=report.public_dict(),
        )

    return synthesize_experience_adapter


def _collect_signals(
    *,
    context_snapshot: dict[str, Any],
    diagnosis: dict[str, Any],
    quality_gate: dict[str, Any],
    delivery: dict[str, Any],
    manual_notes: str,
) -> list[ExperienceSignal]:
    signals: list[ExperienceSignal] = []
    note = _safe_text(manual_notes, limit=700)
    if note:
        signals.append(
            ExperienceSignal(
                signal_ref=_candidate_ref("signal", "manual", note),
                source="manual_notes",
                kind="manual_reflection",
                summary=note,
                evidence_refs=["evidence:l6_20_manual_note"],
                severity="P3",
                confidence=0.78,
            )
        )

    for index, record in enumerate(context_snapshot.get("recent", []) if isinstance(context_snapshot, dict) else []):
        if not isinstance(record, dict):
            continue
        status = _safe_text(record.get("status"), limit=80).lower()
        risk_notes = record.get("risk_notes") or []
        summary = _safe_text(record.get("summary"), limit=500)
        if status not in {"ok", ""} or risk_notes:
            signals.append(
                ExperienceSignal(
                    signal_ref=_candidate_ref("signal", "context", index, status, summary),
                    source="context_memory",
                    kind="runtime_outcome",
                    summary=summary or f"运行状态需要复盘：{status}",
                    evidence_refs=[_safe_text(record.get("record_id"), limit=120) or f"context:{index}"],
                    severity="P2" if status not in {"ok", ""} else "P3",
                    confidence=0.68,
                )
            )

    for item in diagnosis.get("issues", []) if isinstance(diagnosis, dict) else []:
        if not isinstance(item, dict):
            continue
        code = _safe_text(item.get("code"), limit=120)
        severity = _safe_text(item.get("severity"), limit=20).upper() or "P3"
        message = _safe_text(item.get("message"), limit=500)
        signals.append(
            ExperienceSignal(
                signal_ref=_candidate_ref("signal", "diagnosis", code, message),
                source="diagnosis",
                kind=f"diagnosis:{code or 'issue'}",
                summary=message or "工程诊断发现待沉淀问题。",
                evidence_refs=[_safe_text(x, limit=180) for x in item.get("evidence", [])[:4]],
                severity=severity if severity in {"P0", "P1", "P2", "P3"} else "P3",
                confidence=0.76,
            )
        )

    decision = _safe_text(quality_gate.get("decision"), limit=60).lower() if isinstance(quality_gate, dict) else ""
    for item in quality_gate.get("issues", []) if isinstance(quality_gate, dict) else []:
        if not isinstance(item, dict):
            continue
        code = _safe_text(item.get("code"), limit=120)
        severity = _safe_text(item.get("severity"), limit=20).upper() or "P3"
        message = _safe_text(item.get("message"), limit=500)
        signals.append(
            ExperienceSignal(
                signal_ref=_candidate_ref("signal", "quality", code, message),
                source="quality_gate",
                kind=f"quality_gate:{code or decision or 'issue'}",
                summary=message or f"质量门状态需要复盘：{decision}",
                evidence_refs=[_safe_text(x, limit=180) for x in item.get("evidence", [])[:4]],
                severity=severity if severity in {"P0", "P1", "P2", "P3"} else "P3",
                confidence=0.80,
            )
        )
    if decision in {"warn", "fail", "blocked"} and not any(signal.source == "quality_gate" for signal in signals):
        signals.append(
            ExperienceSignal(
                signal_ref=_candidate_ref("signal", "quality_decision", decision),
                source="quality_gate",
                kind=f"quality_gate:{decision}",
                summary=f"质量门 decision={decision}，需要形成复盘候选。",
                evidence_refs=["quality:l6_18_last_verdict"],
                severity="P1" if decision in {"fail", "blocked"} else "P2",
                confidence=0.74,
            )
        )

    if isinstance(delivery, dict):
        release_gate = delivery.get("release_gate", {}) if isinstance(delivery.get("release_gate", {}), dict) else {}
        release_decision = _safe_text(release_gate.get("decision"), limit=80).lower()
        if release_decision in {"warn", "blocked", "fail"}:
            signals.append(
                ExperienceSignal(
                    signal_ref=_candidate_ref("signal", "release_gate", release_decision),
                    source="delivery_manifest",
                    kind=f"release_gate:{release_decision}",
                    summary=f"发布门 decision={release_decision}，交付链需要复盘候选。",
                    evidence_refs=["delivery:l6_19_release_gate"],
                    severity="P2" if release_decision == "warn" else "P1",
                    confidence=0.74,
                )
            )
    return _dedupe_signals(signals)


def _build_lessons(signals: list[ExperienceSignal]) -> list[LessonCandidate]:
    lessons: list[LessonCandidate] = []
    for signal in signals:
        kind = signal.kind.lower()
        if "missing_tests" in kind or "pytest_missing" in kind or "test" in signal.summary.lower():
            lesson_type = "quality_validation"
            summary = "缺少测试或 pytest 证据时，经验应沉淀为“先补最小复测锚点，再进入发布链”。"
            condition = "项目存在 tests 缺口、质量门要求 pytest，或诊断报告显示复测锚点不足。"
            anti_pattern = "跳过复测直接宣称可发布。"
        elif "missing_readme" in kind or "readme" in signal.summary.lower():
            lesson_type = "project_entry_documentation"
            summary = "项目缺少 README / 入口说明时，应沉淀为“先补启动、测试、边界说明”的交付经验。"
            condition = "扫描或诊断发现 README / 使用说明缺失。"
            anti_pattern = "没有入口说明就交给下一轮工程链。"
        elif "quality_gate" in kind or "release_gate" in kind:
            lesson_type = "gate_control"
            summary = "质量门或发布门出现 warn/fail/blocked 时，应沉淀为候选修复经验，不得绕过门禁直接打包。"
            condition = "质量门或发布门 decision 不是 pass。"
            anti_pattern = "用手动 zip 或裸写文件绕过 gate。"
        elif "manual_reflection" in kind:
            lesson_type = "manual_reflection"
            summary = f"人工复盘信号应转化为候选经验：{signal.summary}"
            condition = "用户或工程师明确提出可复用经验、问题或沉淀要求。"
            anti_pattern = "把人工经验只停留在聊天文本，不进入候选链。"
        else:
            lesson_type = "runtime_recovery"
            summary = "非 OK 运行结果或风险摘要应沉淀为可复用排障经验，并保留验证与回滚要求。"
            condition = "Runtime 结果非 OK、存在风险摘要，或工程诊断发现 P1/P2。"
            anti_pattern = "只修当前问题，不生成可复用候选。"
        lessons.append(
            LessonCandidate(
                lesson_ref=_candidate_ref("lesson", signal.signal_ref, lesson_type, summary),
                source_signal_refs=[signal.signal_ref],
                lesson_type=lesson_type,
                summary=summary,
                reusable_condition=condition,
                anti_pattern=anti_pattern,
                confidence=min(0.90, signal.confidence + 0.06),
            )
        )
    return _dedupe_lessons(lessons)


def _build_skill_candidates(lessons: list[LessonCandidate]) -> list[SkillCandidate]:
    candidates: list[SkillCandidate] = []
    for lesson in lessons:
        if lesson.lesson_type == "quality_validation":
            name = "质量门失败复盘与最小复测 Skill 候选"
            purpose = "把缺失测试、pytest 失败、compileall 失败转化为可执行前的修复/复测策略。"
            trigger = "质量门 fail/warn、诊断出现 missing_tests、pytest_missing 或 quality_check_failed。"
        elif lesson.lesson_type == "project_entry_documentation":
            name = "项目入口说明补全 Skill 候选"
            purpose = "指导生成 README、启动方式、测试方式和边界声明，不直接写入项目。"
            trigger = "项目缺少 README 或交付说明。"
        elif lesson.lesson_type == "gate_control":
            name = "质量门与发布门治理 Skill 候选"
            purpose = "在发布前统一检查 pass/warn/fail/blocked，并生成披露与阻断建议。"
            trigger = "质量门或 Release Gate 非 pass。"
        elif lesson.lesson_type == "manual_reflection":
            name = "人工复盘沉淀 Skill 候选"
            purpose = "把人工总结转成可复用操作原则、触发条件与验证要求。"
            trigger = "用户要求总结经验、沉淀方法或形成后续标准动作。"
        else:
            name = "运行失败排障 Skill 候选"
            purpose = "把失败结果、风险摘要和恢复路径沉淀为下次可复用排障策略。"
            trigger = "Runtime 结果非 OK 或风险摘要出现。"
        candidates.append(
            SkillCandidate(
                candidate_ref=_candidate_ref("skill_candidate", lesson.lesson_ref, name),
                source_lesson_refs=[lesson.lesson_ref],
                skill_name=name,
                purpose=purpose,
                trigger_hint=trigger,
                validation_refs=[_candidate_ref("validation", lesson.lesson_ref, name)],
                rollback_refs=[_candidate_ref("rollback", lesson.lesson_ref, name)],
            )
        )
    return _dedupe_by_attr(candidates, "skill_name")


def _build_tool_gap_candidates(lessons: list[LessonCandidate]) -> list[ToolGapCandidate]:
    candidates: list[ToolGapCandidate] = []
    for lesson in lessons:
        if lesson.lesson_type == "quality_validation":
            candidates.append(
                ToolGapCandidate(
                    candidate_ref=_candidate_ref("tool_gap", lesson.lesson_ref, "minimal_test_scaffold"),
                    source_lesson_refs=[lesson.lesson_ref],
                    tool_gap_name="最小复测脚手架 Tool 缺口候选",
                    capability_need="在受控沙箱中根据项目结构生成 smoke test 需求草案，但不直接写测试文件。",
                    governance_requirement="必须经 L4 工具适配、L5 插件宿主登记、L6 质量门验证后才可释放。",
                    validation_refs=[_candidate_ref("validation", lesson.lesson_ref, "minimal_test_scaffold")],
                )
            )
        elif lesson.lesson_type == "gate_control":
            candidates.append(
                ToolGapCandidate(
                    candidate_ref=_candidate_ref("tool_gap", lesson.lesson_ref, "gate_evidence_packager"),
                    source_lesson_refs=[lesson.lesson_ref],
                    tool_gap_name="质量门证据归档 Tool 缺口候选",
                    capability_need="把 compileall / pytest / diagnosis / release gate 摘要统一整理为证据索引候选。",
                    governance_requirement="只允许摘要化证据，不读取或打包敏感文件；发布前必须走 Release Gate。",
                    validation_refs=[_candidate_ref("validation", lesson.lesson_ref, "gate_evidence_packager")],
                )
            )
        elif lesson.lesson_type == "project_entry_documentation":
            candidates.append(
                ToolGapCandidate(
                    candidate_ref=_candidate_ref("tool_gap", lesson.lesson_ref, "readme_outline_builder"),
                    source_lesson_refs=[lesson.lesson_ref],
                    tool_gap_name="README 提纲生成 Tool 缺口候选",
                    capability_need="根据项目索引生成 README 提纲候选，不直接覆盖用户文件。",
                    governance_requirement="需经用户确认后才能由既有 write_workspace_file 写入。",
                    validation_refs=[_candidate_ref("validation", lesson.lesson_ref, "readme_outline_builder")],
                )
            )
    return _dedupe_by_attr(candidates, "tool_gap_name")


def _build_governance_transfers(
    skill_candidates: list[SkillCandidate],
    tool_gap_candidates: list[ToolGapCandidate],
    lessons: list[LessonCandidate],
) -> list[GovernanceTransferItem]:
    transfers: list[GovernanceTransferItem] = []
    for item in skill_candidates:
        transfers.append(
            GovernanceTransferItem(
                transfer_ref=_candidate_ref("transfer", item.candidate_ref, "skill_chain"),
                target_chain="L3/L4/L5 Skill 治理链",
                source_candidate_refs=[item.candidate_ref],
                required_gate="Skill 验证需求 + 回滚需求 + 人工确认",
                summary=f"转交 Skill 候选：{item.skill_name}。当前不注册、不可见、不写 Skill。",
            )
        )
    for item in tool_gap_candidates:
        transfers.append(
            GovernanceTransferItem(
                transfer_ref=_candidate_ref("transfer", item.candidate_ref, "tool_chain"),
                target_chain="L4 工具适配 / L5 插件宿主 / L6 质量门",
                source_candidate_refs=[item.candidate_ref],
                required_gate="沙箱生成计划 + 安全扫描 + 测试验证 + Release Gate",
                summary=f"转交 Tool 缺口候选：{item.tool_gap_name}。当前不生产 Tool、不释放句柄。",
            )
        )
    if lessons and not transfers:
        refs = [lesson.lesson_ref for lesson in lessons[:6]]
        transfers.append(
            GovernanceTransferItem(
                transfer_ref=_candidate_ref("transfer", refs, "lesson_archive_candidate"),
                target_chain="L6 经验候选审阅链",
                source_candidate_refs=refs,
                required_gate="人工审阅 + 候选去重 + 后续版本化",
                summary="仅形成经验候选，等待后续 Skill / Tool 治理链吸收。",
            )
        )
    return transfers


def _build_summary(
    signals: list[ExperienceSignal],
    lessons: list[LessonCandidate],
    skills: list[SkillCandidate],
    tools: list[ToolGapCandidate],
) -> str:
    if not signals:
        return "未发现可沉淀经验信号；当前不会伪造 Skill / Tool 候选。"
    p0p1 = sum(1 for item in signals if item.severity in {"P0", "P1"})
    return (
        f"已从安全摘要中提取 {len(signals)} 个经验信号，形成 {len(lessons)} 条教训候选、"
        f"{len(skills)} 个 Skill 候选、{len(tools)} 个 Tool 缺口候选。"
        f"其中 P0/P1 信号 {p0p1} 个。所有输出均为候选，不执行写入、注册、生产或发布。"
    )


def _dedupe_signals(items: list[ExperienceSignal]) -> list[ExperienceSignal]:
    seen: set[str] = set()
    result: list[ExperienceSignal] = []
    for item in items:
        key = item.signal_ref
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _dedupe_lessons(items: list[LessonCandidate]) -> list[LessonCandidate]:
    seen: set[tuple[str, str]] = set()
    result: list[LessonCandidate] = []
    for item in items:
        key = (item.lesson_type, item.summary)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _dedupe_by_attr(items: list[Any], attr: str) -> list[Any]:
    seen: set[str] = set()
    result: list[Any] = []
    for item in items:
        key = str(getattr(item, attr))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result
