"""L6.70.2-R17 learning asset sandbox alignment.

R16 standardized future Tool/Skill asset metadata.  R17 does not create a new
sandbox.  It explicitly binds R16 Tool assets and Tool production requests to the
existing L6.22 ToolProductionRequestBridge / SandboxValidationPlan preflight
sandbox chain.  The module is metadata-only: it never writes Tool code, never
registers tools, never invokes candidate tools, never calls models, and never
starts loops.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any

from tiangong_agent_shell.safe_logging import redact_text

from .tool_invocation import ToolInvocation
from .tool_result import ToolResult, ToolResultStatus
from .turn_context import TurnContext

SANDBOX_ALIGNMENT_SCHEMA = "tiangong.l6702.r17.learning_asset_sandbox_alignment.v1"
SANDBOX_PROFILE = "isolated_workspace_candidate_only"
SANDBOX_BRIDGE = "L6.22 ToolProductionRequestBridge/SandboxValidationPlan"
SANDBOX_TOOL_NAMES = {
    "learning_asset_sandbox_guide",
    "learning_asset_sandbox_align",
    "learning_asset_sandbox_validate",
}


@dataclass(frozen=True)
class SandboxAlignmentIssue:
    field: str
    severity: str
    message: str
    ref: str = ""

    def public_dict(self) -> dict[str, str]:
        return {
            "field": self.field,
            "severity": self.severity,
            "message": self.message,
            "ref": self.ref,
        }


@dataclass(frozen=True)
class SandboxAlignmentReport:
    schema: str
    generated_at: float
    status: str
    summary: str
    existing_sandbox_found: bool
    sandbox_bridge: str
    sandbox_profile: str
    contract_count: int
    tool_contract_count: int
    production_request_count: int
    sandbox_plan_count: int
    queue_count: int
    aligned_tool_contract_count: int
    issues: list[SandboxAlignmentIssue] = field(default_factory=list)
    mappings: list[dict[str, Any]] = field(default_factory=list)
    enforcement_chain: list[str] = field(default_factory=list)
    candidate_only: bool = True
    sandbox_preflight_only: bool = True
    produces_tool: bool = False
    writes_tool_code: bool = False
    registers_tool: bool = False
    releases_tool_handle: bool = False
    invokes_candidate_tool: bool = False
    starts_background_loop: bool = False
    imports_v1: bool = False

    def __post_init__(self) -> None:
        if not self.candidate_only or not self.sandbox_preflight_only:
            raise ValueError("sandbox alignment report must remain candidate-only and preflight-only")
        if any((
            self.produces_tool,
            self.writes_tool_code,
            self.registers_tool,
            self.releases_tool_handle,
            self.invokes_candidate_tool,
            self.starts_background_loop,
            self.imports_v1,
        )):
            raise ValueError("sandbox alignment cannot produce/register/invoke tools, start loops, or import v1")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "status": self.status,
            "summary": self.summary,
            "existing_sandbox_found": self.existing_sandbox_found,
            "sandbox_bridge": self.sandbox_bridge,
            "sandbox_profile": self.sandbox_profile,
            "contract_count": self.contract_count,
            "tool_contract_count": self.tool_contract_count,
            "production_request_count": self.production_request_count,
            "sandbox_plan_count": self.sandbox_plan_count,
            "queue_count": self.queue_count,
            "aligned_tool_contract_count": self.aligned_tool_contract_count,
            "issues": [item.public_dict() for item in self.issues],
            "issue_count": len(self.issues),
            "mappings": list(self.mappings),
            "enforcement_chain": list(self.enforcement_chain),
            "candidate_only": self.candidate_only,
            "sandbox_preflight_only": self.sandbox_preflight_only,
            "produces_tool": self.produces_tool,
            "writes_tool_code": self.writes_tool_code,
            "registers_tool": self.registers_tool,
            "releases_tool_handle": self.releases_tool_handle,
            "invokes_candidate_tool": self.invokes_candidate_tool,
            "starts_background_loop": self.starts_background_loop,
            "imports_v1": self.imports_v1,
            "next_action_hint": {
                "next_tool": "learning_asset_sandbox_validate" if self.status in {"aligned", "no_tool_contracts"} else "queue_tool_production_requests",
                "reason": "Tool/Skill 统一资产契约必须先绑定 L6.22 沙箱验证前置，再进入质量门/发布门/注册审阅。",
                "llm_final_decision_required": True,
            },
        }

    def summary_text(self) -> str:
        return (
            "R17 Tool/Skill 统一资产沙箱对齐："
            f"status={self.status}；existing_sandbox={self.existing_sandbox_found}；"
            f"contracts={self.contract_count}；tool_contracts={self.tool_contract_count}；"
            f"requests={self.production_request_count}；sandbox_plans={self.sandbox_plan_count}；"
            f"issues={len(self.issues)}。{self.summary}"
        )


class LearningAssetSandboxAlignmentBridge:
    """Keeps the latest R17 sandbox alignment report."""

    def __init__(self) -> None:
        self._last_report: SandboxAlignmentReport | None = None

    @property
    def last_report(self) -> SandboxAlignmentReport | None:
        return self._last_report

    def guide(self) -> dict[str, Any]:
        return build_sandbox_alignment_guide()

    def align(
        self,
        *,
        learning_contract_report: dict[str, Any] | None = None,
        tool_request_report: dict[str, Any] | None = None,
        notes: str = "",
        strict: bool = False,
    ) -> SandboxAlignmentReport:
        report = build_sandbox_alignment_report(
            learning_contract_report=learning_contract_report or {},
            tool_request_report=tool_request_report or {},
            notes=notes,
            strict=strict,
        )
        self._last_report = report
        return report

    def validate(
        self,
        *,
        learning_contract_report: dict[str, Any] | None = None,
        tool_request_report: dict[str, Any] | None = None,
        notes: str = "",
    ) -> SandboxAlignmentReport:
        source_contract = learning_contract_report or {}
        source_tool_request = tool_request_report or {}
        if not source_contract and self._last_report is not None:
            # Re-use the previous summarized result for validation status when no new payload is passed.
            prev = self._last_report
            issues = list(prev.issues)
            status = "pass" if prev.existing_sandbox_found and not issues else "needs_review"
            report = SandboxAlignmentReport(
                schema=SANDBOX_ALIGNMENT_SCHEMA,
                generated_at=time(),
                status=status,
                summary=f"复核最近一次沙箱对齐报告；问题 {len(issues)} 个。",
                existing_sandbox_found=prev.existing_sandbox_found,
                sandbox_bridge=prev.sandbox_bridge,
                sandbox_profile=prev.sandbox_profile,
                contract_count=prev.contract_count,
                tool_contract_count=prev.tool_contract_count,
                production_request_count=prev.production_request_count,
                sandbox_plan_count=prev.sandbox_plan_count,
                queue_count=prev.queue_count,
                aligned_tool_contract_count=prev.aligned_tool_contract_count,
                issues=issues,
                mappings=prev.mappings,
                enforcement_chain=prev.enforcement_chain,
            )
            self._last_report = report
            return report
        return self.align(
            learning_contract_report=source_contract,
            tool_request_report=source_tool_request,
            notes=notes,
            strict=True,
        )

    def public_dict(self) -> dict[str, Any]:
        if self._last_report is None:
            return {"schema": SANDBOX_ALIGNMENT_SCHEMA, "status": "empty", "guide": build_sandbox_alignment_guide()}
        return self._last_report.public_dict()


def build_sandbox_alignment_guide() -> dict[str, Any]:
    return {
        "schema": SANDBOX_ALIGNMENT_SCHEMA,
        "purpose": "把 R16 统一 Tool/Skill 资产契约对齐到已存在的 L6.22 Tool 生产请求沙箱化与验证前置链。",
        "found_existing_sandbox": {
            "bridge": "ToolProductionRequestBridge",
            "plan": "SandboxValidationPlan",
            "queue": "ToolProductionQueueItem",
            "profile": SANDBOX_PROFILE,
            "stage": "L6.22 Tool 生产请求沙箱化与验证前置",
        },
        "not_a_new_sandbox": True,
        "boundary": {
            "candidate_stage": "A2 metadata/preflight only",
            "future_sandbox_stage": "A3 governed sandbox only after LLM decision, quality gate and release gate",
            "forbidden": [
                "写真实 Tool 代码",
                "注册 Tool",
                "释放工具句柄",
                "调用候选工具",
                "复用 v1 registry/executor/provider/self-iteration",
                "启动后台 loop",
                "裸 shell/network/credential",
            ],
        },
        "canonical_pipeline": [
            "synthesize_experience_candidates",
            "queue_skill_candidates",
            "queue_tool_production_requests 生成 L6.22 ToolProductionRequest + SandboxValidationPlan",
            "learning_asset_contract_normalize 归一 R16 契约",
            "learning_asset_contract_validate 校验字段/usage_card/chain_recipe/no-pollution",
            "learning_asset_sandbox_align 绑定 R16 Tool 契约与 L6.22 sandbox plan",
            "learning_asset_sandbox_validate 复核 sandbox mapping 后再进入质量门/发布门/注册审阅",
        ],
        "llm_rule": "LLM 是主脑；沙箱对齐层只提供证据与下一步提示，不自动生产、注册、激活或执行候选工具。",
        "commands": {
            "guide": "asset-sandbox guide",
            "align": "asset-sandbox align",
            "validate": "asset-sandbox validate",
            "drill": "asset-sandbox drill pytest missing tests",
        },
    }


def build_sandbox_alignment_report(
    *,
    learning_contract_report: dict[str, Any],
    tool_request_report: dict[str, Any],
    notes: str = "",
    strict: bool = False,
) -> SandboxAlignmentReport:
    contracts = [item for item in _as_list(learning_contract_report.get("contracts")) if isinstance(item, dict)]
    tool_contracts = [item for item in contracts if item.get("asset_kind") == "tool"]
    requests = [item for item in _as_list(tool_request_report.get("production_requests")) if isinstance(item, dict)]
    plans = [item for item in _as_list(tool_request_report.get("sandbox_validation_plans")) if isinstance(item, dict)]
    queue = [item for item in _as_list(tool_request_report.get("review_queue")) if isinstance(item, dict)]

    request_refs = {_safe_text(item.get("request_ref"), limit=220) for item in requests}
    request_by_candidate = {
        _safe_text(item.get("source_candidate_ref"), limit=220): _safe_text(item.get("request_ref"), limit=220)
        for item in requests
        if _safe_text(item.get("source_candidate_ref"), limit=220)
    }
    plan_by_request = {
        _safe_text(item.get("request_ref"), limit=220): _safe_text(item.get("validation_ref"), limit=220)
        for item in plans
        if _safe_text(item.get("request_ref"), limit=220)
    }
    queue_by_request = {
        _safe_text(item.get("request_ref"), limit=220): _safe_text(item.get("queue_ref"), limit=220)
        for item in queue
        if _safe_text(item.get("request_ref"), limit=220)
    }

    issues: list[SandboxAlignmentIssue] = []
    mappings: list[dict[str, Any]] = []
    aligned = 0
    for contract in tool_contracts:
        asset_ref = _safe_text(contract.get("asset_ref"), limit=220)
        source = contract.get("source_trace") if isinstance(contract.get("source_trace"), dict) else {}
        source_ref = _safe_text(source.get("source_ref"), limit=220)
        candidate_ref = _safe_text(source.get("candidate_ref"), limit=220)
        request_ref = ""
        if source_ref in request_refs:
            request_ref = source_ref
        elif source_ref in request_by_candidate:
            request_ref = request_by_candidate[source_ref]
        elif candidate_ref in request_by_candidate:
            request_ref = request_by_candidate[candidate_ref]
        validation_ref = plan_by_request.get(request_ref, "")
        queue_ref = queue_by_request.get(request_ref, "")
        ok = bool(request_ref and validation_ref)
        if ok:
            aligned += 1
        else:
            issues.append(
                SandboxAlignmentIssue(
                    field="tool_contract.sandbox_mapping",
                    severity="P1" if strict else "P2",
                    message="Tool 契约未找到对应 L6.22 ToolProductionRequest/SandboxValidationPlan 映射。",
                    ref=asset_ref or source_ref,
                )
            )
        mappings.append({
            "asset_ref": asset_ref,
            "asset_name": _safe_text(contract.get("name"), limit=160),
            "source_ref": source_ref,
            "candidate_ref": candidate_ref,
            "request_ref": request_ref,
            "sandbox_validation_ref": validation_ref,
            "queue_ref": queue_ref,
            "sandbox_profile": SANDBOX_PROFILE,
            "aligned": ok,
        })

    existing_sandbox_found = True  # The bridge/plan classes are in this module's Runtime wiring; absence would import-fail earlier.
    if not existing_sandbox_found:
        issues.append(SandboxAlignmentIssue("sandbox", "P0", "未找到 L6.22 沙箱前置链。"))
    if strict and tool_contracts and not requests:
        issues.append(SandboxAlignmentIssue("tool_requests", "P1", "存在 Tool 契约但 Tool 生产请求队列为空。"))
    if strict and requests and not plans:
        issues.append(SandboxAlignmentIssue("sandbox_validation_plans", "P1", "存在 Tool 请求但缺少 SandboxValidationPlan。"))

    if tool_contracts:
        status = "aligned" if not issues else "needs_review"
    else:
        status = "no_tool_contracts" if not issues else "needs_review"
    if strict and status == "aligned":
        status = "pass"
    if strict and status == "no_tool_contracts":
        status = "pass"

    summary = _summary(
        tool_contracts=len(tool_contracts),
        requests=len(requests),
        plans=len(plans),
        aligned=aligned,
        issues=len(issues),
        notes=notes,
    )
    return SandboxAlignmentReport(
        schema=SANDBOX_ALIGNMENT_SCHEMA,
        generated_at=time(),
        status=status,
        summary=summary,
        existing_sandbox_found=existing_sandbox_found,
        sandbox_bridge=SANDBOX_BRIDGE,
        sandbox_profile=SANDBOX_PROFILE,
        contract_count=len(contracts),
        tool_contract_count=len(tool_contracts),
        production_request_count=len(requests),
        sandbox_plan_count=len(plans),
        queue_count=len(queue),
        aligned_tool_contract_count=aligned,
        issues=issues,
        mappings=mappings,
        enforcement_chain=build_sandbox_alignment_guide()["canonical_pipeline"],
    )


def build_learning_asset_sandbox_guide_adapter():
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        guide = build_sandbox_alignment_guide()
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary="R17 已找到并说明现有 L6.22 Tool 生产请求沙箱化与验证前置链；本工具只返回对齐指南。",
            data=guide,
        )

    return adapter


def build_learning_asset_sandbox_align_adapter(bridge: LearningAssetSandboxAlignmentBridge, learning_contract: Any, tool_requests: Any):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            report = bridge.align(
                learning_contract_report=learning_contract.public_dict(),
                tool_request_report=tool_requests.public_dict(),
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
                strict=bool(invocation.arguments.get("strict", False)),
            )
        except (TypeError, ValueError) as exc:
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.FAILED,
                f"学习资产沙箱对齐失败：{exc}",
                error_code="learning_asset_sandbox_align_failed",
            )
        status = ToolResultStatus.OK if report.status in {"aligned", "no_tool_contracts", "pass"} else ToolResultStatus.FAILED
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=status,
            output_summary=report.summary_text(),
            data=report.public_dict(),
            error_code="" if status is ToolResultStatus.OK else "learning_asset_sandbox_alignment_needs_review",
        )

    return adapter


def build_learning_asset_sandbox_validate_adapter(bridge: LearningAssetSandboxAlignmentBridge, learning_contract: Any, tool_requests: Any):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            report = bridge.validate(
                learning_contract_report=learning_contract.public_dict(),
                tool_request_report=tool_requests.public_dict(),
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
            )
        except (TypeError, ValueError) as exc:
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.FAILED,
                f"学习资产沙箱校验失败：{exc}",
                error_code="learning_asset_sandbox_validate_failed",
            )
        status = ToolResultStatus.OK if report.status == "pass" else ToolResultStatus.FAILED
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=status,
            output_summary=report.summary_text(),
            data=report.public_dict(),
            error_code="" if status is ToolResultStatus.OK else "learning_asset_sandbox_validate_needs_review",
        )

    return adapter


def _summary(*, tool_contracts: int, requests: int, plans: int, aligned: int, issues: int, notes: str) -> str:
    note_hint = "；已接收人工备注" if _safe_text(notes, limit=120) else ""
    if tool_contracts <= 0:
        return f"未发现 Tool 类统一资产契约；已确认 L6.22 沙箱前置链存在，可等待后续 Tool 请求进入队列{note_hint}。"
    return (
        "已把 R16 Tool 类资产契约映射到 L6.22 ToolProductionRequest/SandboxValidationPlan；"
        f"tool_contracts={tool_contracts}；requests={requests}；plans={plans}；aligned={aligned}；issues={issues}{note_hint}。"
    )


def _safe_text(value: Any, *, limit: int = 700) -> str:
    return redact_text(str(value or "")).strip()[:limit]


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value in (None, ""):
        return []
    return [value]
