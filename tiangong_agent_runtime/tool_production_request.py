"""L6.22 Tool 生产请求沙箱化与验证前置。

该模块只把 L6.20 经验沉淀产生的 ToolGapCandidate 转成 Runtime 外壳层
ToolProductionRequest、SandboxValidationPlan 与待验证队列。它面向 LLM 执行力优先：
发现缺工具、生成生产请求、形成沙箱验证计划、入队和导出默认放开；但本阶段不写
工具代码、不注册 Tool、不释放工具句柄、不调用新工具、不绕过 L4 工具适配与 L5 插件宿主。
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

TOOL_REQUEST_SCHEMA = "tiangong.l6_22.tool_production_request.v1"
SENSITIVE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer|token|secret|password|credential)\s*[:=]\s*[^\s,;]+"
)
SENSITIVE_WORDS = ("api_key", "apikey", "authorization", "bearer", "token", "secret", "password", "credential")


@dataclass(frozen=True)
class ToolProductionRequest:
    """Tool 生产请求。

    这是“缺工具”到“可被沙箱生产链处理”的请求外壳，不是 ToolPackage、不是
    真实工具代码、不是注册表记录。后续真实生产必须经 L4/L5/L6 治理链。
    """

    request_ref: str
    source_candidate_ref: str
    source_lesson_refs: list[str]
    tool_name_hint: str
    capability_need: str
    governance_requirement: str
    requested_interface: str = "ToolPackageCandidateSpec"
    status: str = "request_ready"
    execution_priority: str = "execution_first"
    validation_refs: list[str] = field(default_factory=list)
    required_tests: list[str] = field(
        default_factory=lambda: [
            "compileall_or_static_check",
            "unit_or_smoke_test_requirement",
            "forbidden_scan",
            "quality_gate",
            "rollback_evidence",
        ]
    )
    sandbox_required: bool = True
    risk_level_hint: str = "A2_request/A3_future_sandbox"
    produces_tool: bool = False
    writes_tool_code: bool = False
    registers_tool: bool = False
    releases_tool_handle: bool = False
    calls_tool: bool = False
    touches_kernel: bool = False

    def __post_init__(self) -> None:
        if not self.sandbox_required:
            raise ValueError("L6.22 ToolProductionRequest must require sandbox validation")
        forbidden = (
            self.produces_tool,
            self.writes_tool_code,
            self.registers_tool,
            self.releases_tool_handle,
            self.calls_tool,
            self.touches_kernel,
        )
        if any(forbidden):
            raise ValueError("L6.22 ToolProductionRequest cannot produce, write, register, release, call or touch kernel")

    def public_dict(self) -> dict[str, Any]:
        return {
            "request_ref": self.request_ref,
            "source_candidate_ref": self.source_candidate_ref,
            "source_lesson_refs": list(self.source_lesson_refs),
            "tool_name_hint": self.tool_name_hint,
            "capability_need": self.capability_need,
            "governance_requirement": self.governance_requirement,
            "requested_interface": self.requested_interface,
            "status": self.status,
            "execution_priority": self.execution_priority,
            "validation_refs": list(self.validation_refs),
            "required_tests": list(self.required_tests),
            "sandbox_required": self.sandbox_required,
            "risk_level_hint": self.risk_level_hint,
            "produces_tool": self.produces_tool,
            "writes_tool_code": self.writes_tool_code,
            "registers_tool": self.registers_tool,
            "releases_tool_handle": self.releases_tool_handle,
            "calls_tool": self.calls_tool,
            "touches_kernel": self.touches_kernel,
        }


@dataclass(frozen=True)
class SandboxValidationPlan:
    """沙箱验证前置计划。

    计划只描述未来沙箱生产链需要执行的验证项目；本阶段不执行 shell、网络、文件写入
    或真实测试，不生成 Tool 产物。
    """

    validation_ref: str
    request_ref: str
    sandbox_profile: str = "isolated_workspace_candidate_only"
    validation_steps: list[str] = field(
        default_factory=lambda: [
            "生成 Tool 规格草案而非代码落盘",
            "静态接口审查：输入/输出/错误码/审计字段",
            "最小 smoke test 需求草案",
            "forbidden scan：密钥、私钥、裸网络、裸模型 SDK、越权路径",
            "L6.18 质量门与 L6.19 发布门前置要求",
            "回滚与隔离证据要求",
        ]
    )
    required_gates: list[str] = field(
        default_factory=lambda: [
            "L4 tool_adapter_boundary",
            "L5 plugin_host_contract",
            "L6.18 quality_gate",
            "L6.19 release_gate",
            "audit_and_rollback_evidence",
        ]
    )
    allow_network: bool = False
    allow_shell: bool = False
    executes_sandbox: bool = False
    produces_tool: bool = False
    writes_tool_code: bool = False
    modifies_code: bool = False

    def __post_init__(self) -> None:
        forbidden = (self.allow_network, self.allow_shell, self.executes_sandbox, self.produces_tool, self.writes_tool_code, self.modifies_code)
        if any(forbidden):
            raise ValueError("L6.22 SandboxValidationPlan is preflight-only and cannot execute/write/produce")

    def public_dict(self) -> dict[str, Any]:
        return {
            "validation_ref": self.validation_ref,
            "request_ref": self.request_ref,
            "sandbox_profile": self.sandbox_profile,
            "validation_steps": list(self.validation_steps),
            "required_gates": list(self.required_gates),
            "allow_network": self.allow_network,
            "allow_shell": self.allow_shell,
            "executes_sandbox": self.executes_sandbox,
            "produces_tool": self.produces_tool,
            "writes_tool_code": self.writes_tool_code,
            "modifies_code": self.modifies_code,
        }


@dataclass(frozen=True)
class ToolProductionQueueItem:
    """Tool 生产请求队列项。"""

    queue_ref: str
    request_ref: str
    validation_ref: str
    source_candidate_ref: str
    status: str = "pending_sandbox_validation"
    priority: str = "P1_execution"
    governance_chain: list[str] = field(default_factory=lambda: ["L6.22 request", "L4 adapter", "L5 host", "L6.18 gate", "L6.19 release"])
    next_action: str = "send_to_sandbox_spec_review"
    applies_change: bool = False
    produces_tool: bool = False
    registers_tool: bool = False
    releases_tool_handle: bool = False
    calls_tool: bool = False

    def __post_init__(self) -> None:
        forbidden = (self.applies_change, self.produces_tool, self.registers_tool, self.releases_tool_handle, self.calls_tool)
        if any(forbidden):
            raise ValueError("L6.22 ToolProductionQueueItem cannot apply, produce, register, release or call tools")

    def public_dict(self) -> dict[str, Any]:
        return {
            "queue_ref": self.queue_ref,
            "request_ref": self.request_ref,
            "validation_ref": self.validation_ref,
            "source_candidate_ref": self.source_candidate_ref,
            "status": self.status,
            "priority": self.priority,
            "governance_chain": list(self.governance_chain),
            "next_action": self.next_action,
            "applies_change": self.applies_change,
            "produces_tool": self.produces_tool,
            "registers_tool": self.registers_tool,
            "releases_tool_handle": self.releases_tool_handle,
            "calls_tool": self.calls_tool,
        }


@dataclass(frozen=True)
class ToolProductionRequestReport:
    schema: str
    generated_at: float
    status: str
    summary: str
    production_requests: list[ToolProductionRequest] = field(default_factory=list)
    sandbox_validation_plans: list[SandboxValidationPlan] = field(default_factory=list)
    review_queue: list[ToolProductionQueueItem] = field(default_factory=list)
    source_report_schema: str = ""
    source_report_status: str = ""
    notes_used: bool = False
    request_only: bool = True
    execution_first: bool = True
    sandbox_preflight_only: bool = True
    produces_tool: bool = False
    writes_tool_code: bool = False
    registers_tool: bool = False
    releases_tool_handle: bool = False
    calls_tool: bool = False
    modifies_code: bool = False
    applies_change: bool = False
    touches_kernel: bool = False

    def __post_init__(self) -> None:
        if not self.request_only or not self.execution_first or not self.sandbox_preflight_only:
            raise ValueError("L6.22 tool request report must remain request-only, execution-first and sandbox-preflight-only")
        forbidden = (
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
            raise ValueError("L6.22 tool request report cannot perform production/registry/tool/code/kernel side effects")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "status": self.status,
            "summary": self.summary,
            "production_requests": [item.public_dict() for item in self.production_requests],
            "sandbox_validation_plans": [item.public_dict() for item in self.sandbox_validation_plans],
            "review_queue": [item.public_dict() for item in self.review_queue],
            "source_report_schema": self.source_report_schema,
            "source_report_status": self.source_report_status,
            "notes_used": self.notes_used,
            "request_only": self.request_only,
            "execution_first": self.execution_first,
            "sandbox_preflight_only": self.sandbox_preflight_only,
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
            "L6.22 Tool 生产请求沙箱化队列："
            f"status={self.status}；requests={len(self.production_requests)}；"
            f"sandbox_plans={len(self.sandbox_validation_plans)}；queue={len(self.review_queue)}；"
            f"request_only={self.request_only}；execution_first={self.execution_first}。{self.summary}"
        )

    def markdown_report(self) -> str:
        lines = [
            "# 临渊者 L6.22 Tool 生产请求沙箱化与验证前置报告",
            "",
            f"- schema: `{self.schema}`",
            f"- status: `{self.status}`",
            f"- request_only: `{self.request_only}`",
            f"- execution_first: `{self.execution_first}`",
            f"- sandbox_preflight_only: `{self.sandbox_preflight_only}`",
            f"- produces_tool: `{self.produces_tool}`",
            f"- registers_tool: `{self.registers_tool}`",
            f"- releases_tool_handle: `{self.releases_tool_handle}`",
            f"- applies_change: `{self.applies_change}`",
            "",
            "## 摘要",
            "",
            self.summary,
            "",
            "## Tool 生产请求",
            "",
        ]
        if not self.production_requests:
            lines.append("暂无 Tool 生产请求。")
        for item in self.production_requests:
            lines.append(f"- `{item.request_ref}` {item.tool_name_hint}: {item.capability_need}")
        lines.extend(["", "## 沙箱验证前置计划", ""])
        if not self.sandbox_validation_plans:
            lines.append("暂无沙箱验证前置计划。")
        for item in self.sandbox_validation_plans:
            lines.append(f"- `{item.validation_ref}` -> `{item.request_ref}` / {item.sandbox_profile}")
        lines.extend(["", "## 队列", ""])
        if not self.review_queue:
            lines.append("暂无队列项。")
        for item in self.review_queue:
            lines.append(f"- `{item.queue_ref}` -> `{item.request_ref}` [{item.priority}] next={item.next_action}")
        lines.append("")
        lines.append("> L6.22 只生成 Tool 生产请求与沙箱验证前置计划；真实 Tool 代码、注册、挂载和句柄释放必须进入后续治理链。")
        return "\n".join(lines)


class ToolProductionRequestBridge:
    """Runtime 外壳层 Tool 生产请求与沙箱验证前置队列。"""

    def __init__(self) -> None:
        self._requests: dict[str, ToolProductionRequest] = {}
        self._plans: dict[str, SandboxValidationPlan] = {}
        self._queue: dict[str, ToolProductionQueueItem] = {}
        self._last_report: ToolProductionRequestReport | None = None

    @property
    def last_report(self) -> ToolProductionRequestReport | None:
        return self._last_report

    def reset(self) -> None:
        self._requests.clear()
        self._plans.clear()
        self._queue.clear()
        self._last_report = None

    def queue_from_experience(
        self,
        *,
        experience_report: dict[str, Any] | None = None,
        notes: str = "",
        max_items: int = 20,
    ) -> ToolProductionRequestReport:
        source = experience_report or {}
        candidates = source.get("tool_gap_candidates", []) if isinstance(source, dict) else []
        limit = max(1, min(int(max_items), 100))
        added = 0
        for candidate in candidates[:limit]:
            if not isinstance(candidate, dict):
                continue
            request = _build_request(candidate)
            if request.request_ref not in self._requests:
                self._requests[request.request_ref] = request
                added += 1
            plan = _build_validation_plan(request)
            if plan.validation_ref not in self._plans:
                self._plans[plan.validation_ref] = plan
            queue_item = _build_queue_item(request, plan)
            if queue_item.queue_ref not in self._queue:
                self._queue[queue_item.queue_ref] = queue_item

        requests = list(self._requests.values())
        plans = list(self._plans.values())
        queue = list(self._queue.values())
        source_status = _safe_text(source.get("status", ""), limit=80) if isinstance(source, dict) else ""
        status = "empty" if not requests else "request_ready"
        if candidates and added == 0 and requests:
            status = "request_ready_no_new"
        summary = _build_summary(
            source_status=source_status,
            source_count=len(candidates) if isinstance(candidates, list) else 0,
            added=added,
            total=len(requests),
            notes=notes,
        )
        report = ToolProductionRequestReport(
            schema=TOOL_REQUEST_SCHEMA,
            generated_at=time(),
            status=status,
            summary=summary,
            production_requests=requests,
            sandbox_validation_plans=plans,
            review_queue=queue,
            source_report_schema=_safe_text(source.get("schema", ""), limit=120) if isinstance(source, dict) else "",
            source_report_status=source_status,
            notes_used=bool(_safe_text(notes, limit=200)),
        )
        self._last_report = report
        return report

    def public_dict(self) -> dict[str, Any]:
        if self._last_report is None:
            if not self._requests:
                return {"schema": TOOL_REQUEST_SCHEMA, "status": "empty", "message": "暂无 Tool 生产请求，请先执行 /tool-request-build。"}
            self._last_report = ToolProductionRequestReport(
                schema=TOOL_REQUEST_SCHEMA,
                generated_at=time(),
                status="request_ready",
                summary=f"已存在 {len(self._requests)} 个 Tool 生产请求、{len(self._plans)} 个沙箱验证前置计划与 {len(self._queue)} 个队列项。",
                production_requests=list(self._requests.values()),
                sandbox_validation_plans=list(self._plans.values()),
                review_queue=list(self._queue.values()),
            )
        return self._last_report.public_dict()

    def export_json(self, path: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def build_planner_hint(self) -> str:
        if not self._requests:
            return ""
        names = ", ".join(item.tool_name_hint for item in list(self._requests.values())[:3]) or "无"
        return f"最近 L6.22 Tool 生产请求：requests={len(self._requests)}; queue={len(self._queue)}; tools={names}; request_only=True; sandbox_preflight_only=True"


def build_queue_tool_production_requests_adapter(tool_requests: ToolProductionRequestBridge, experience: Any):
    def queue_tool_production_requests_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            report = tool_requests.queue_from_experience(
                experience_report=experience.public_dict(),
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
                max_items=int(invocation.arguments.get("max_items") or 20),
            )
        except (TypeError, ValueError) as exc:
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.FAILED,
                f"Tool 生产请求入队失败：{exc}",
                error_code="tool_request_failed",
            )
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=report.summary_text(),
            data=report.public_dict(),
        )

    return queue_tool_production_requests_adapter


def _build_request(candidate: dict[str, Any]) -> ToolProductionRequest:
    candidate_ref = _safe_text(candidate.get("candidate_ref"), limit=160) or _ref("tool_gap", candidate)
    name = _safe_text(candidate.get("tool_gap_name"), limit=140) or "未命名 Tool 缺口候选"
    capability_need = _safe_text(candidate.get("capability_need"), limit=900) or "待补充能力需求。"
    governance_requirement = _safe_text(candidate.get("governance_requirement"), limit=700) or "必须经 L4/L5/L6 治理链后才可释放。"
    source_lesson_refs = [_safe_text(item, limit=160) for item in _as_list(candidate.get("source_lesson_refs"))[:20]]
    validation_refs = [_safe_text(item, limit=160) for item in _as_list(candidate.get("validation_refs"))[:20]]
    return ToolProductionRequest(
        request_ref=_ref("tool_request", candidate_ref, name, capability_need, governance_requirement),
        source_candidate_ref=candidate_ref,
        source_lesson_refs=source_lesson_refs,
        tool_name_hint=name,
        capability_need=capability_need,
        governance_requirement=governance_requirement,
        validation_refs=validation_refs,
    )


def _build_validation_plan(request: ToolProductionRequest) -> SandboxValidationPlan:
    return SandboxValidationPlan(
        validation_ref=_ref("sandbox_validation", request.request_ref, request.tool_name_hint),
        request_ref=request.request_ref,
    )


def _build_queue_item(request: ToolProductionRequest, plan: SandboxValidationPlan) -> ToolProductionQueueItem:
    return ToolProductionQueueItem(
        queue_ref=_ref("tool_request_queue", request.request_ref, plan.validation_ref),
        request_ref=request.request_ref,
        validation_ref=plan.validation_ref,
        source_candidate_ref=request.source_candidate_ref,
    )


def _build_summary(*, source_status: str, source_count: int, added: int, total: int, notes: str) -> str:
    note_hint = "；已接收人工备注" if _safe_text(notes, limit=120) else ""
    if total <= 0:
        return f"未发现可转化为 Tool 生产请求的 Tool 缺口候选。source_status={source_status or 'empty'}；source_candidates={source_count}{note_hint}。"
    return (
        "Tool 缺口候选已转成生产请求、沙箱验证前置计划并进入队列；"
        f"source_status={source_status or 'unknown'}；source_candidates={source_count}；"
        f"本次新增={added}；队列累计={total}{note_hint}。"
        "请求可继续排序、审阅、导出和转交，但不会自动写工具代码、注册 Tool 或释放工具句柄。"
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
    return f"{prefix}:l6_22_{digest}"


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value in (None, ""):
        return []
    return [value]
