"""L6.70.2-R19 simplified Tool/Skill candidate release gate.

R18 already materializes isolated Tool/Skill candidate packages. R19 intentionally
keeps the next step small: one gate turns the latest R18 candidate evidence into
four direct LLM-facing verdicts: quality gate, release gate, rollback evidence,
and registration request readiness.

Boundary: R19 writes only a metadata request file under
``.linyuanzhe/candidate_sandbox/r19``. It never writes the real Skill registry,
never registers Runtime tools, never activates Skills, never releases handles,
never invokes candidate tools, never calls models/network/shell, and never starts
background loops. LLM remains the final decider.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import Any

from .tool_invocation import ToolInvocation
from .tool_result import ToolResult, ToolResultStatus
from .turn_context import TurnContext
from .workspace_guard import WorkspaceGuard, WorkspaceViolation

RELEASE_GATE_SCHEMA = "tiangong.l6702.r19.learning_asset_release_gate.v1"
RELEASE_GATE_ROOT = ".linyuanzhe/candidate_sandbox/r19"
RELEASE_GATE_TOOL_NAMES = {
    "learning_asset_release_gate_guide",
    "learning_asset_release_gate_check",
}


@dataclass(frozen=True)
class ReleaseGateIssue:
    field: str
    severity: str
    message: str
    ref: str = ""

    def public_dict(self) -> dict[str, str]:
        return {"field": self.field, "severity": self.severity, "message": self.message, "ref": self.ref}


@dataclass(frozen=True)
class ReleaseGateReport:
    schema: str
    generated_at: float
    status: str
    summary: str
    workspace_root: str
    report_path: str
    source_candidate_status: str
    package_count: int
    quality_gate: dict[str, Any]
    release_gate: dict[str, Any]
    rollback_evidence: dict[str, Any]
    registration_request: dict[str, Any]
    issues: list[ReleaseGateIssue] = field(default_factory=list)
    chain: list[str] = field(default_factory=list)
    writes_real_skill_registry: bool = False
    registers_runtime_tool: bool = False
    activates_skill: bool = False
    releases_tool_handle: bool = False
    invokes_candidate_tool: bool = False
    dispatches_model: bool = False
    starts_background_loop: bool = False
    imports_v1: bool = False
    copies_v1_source: bool = False

    def __post_init__(self) -> None:
        if any((
            self.writes_real_skill_registry,
            self.registers_runtime_tool,
            self.activates_skill,
            self.releases_tool_handle,
            self.invokes_candidate_tool,
            self.dispatches_model,
            self.starts_background_loop,
            self.imports_v1,
            self.copies_v1_source,
        )):
            raise ValueError("R19 release gate crossed activation/registration/pollution boundary")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "status": self.status,
            "summary": self.summary,
            "workspace_root": self.workspace_root,
            "report_path": self.report_path,
            "source_candidate_status": self.source_candidate_status,
            "package_count": self.package_count,
            "quality_gate": self.quality_gate,
            "release_gate": self.release_gate,
            "rollback_evidence": self.rollback_evidence,
            "registration_request": self.registration_request,
            "issues": [issue.public_dict() for issue in self.issues],
            "issue_count": len(self.issues),
            "chain": list(self.chain),
            "writes_real_skill_registry": self.writes_real_skill_registry,
            "registers_runtime_tool": self.registers_runtime_tool,
            "activates_skill": self.activates_skill,
            "releases_tool_handle": self.releases_tool_handle,
            "invokes_candidate_tool": self.invokes_candidate_tool,
            "dispatches_model": self.dispatches_model,
            "starts_background_loop": self.starts_background_loop,
            "imports_v1": self.imports_v1,
            "copies_v1_source": self.copies_v1_source,
            "next_action_hint": {
                "next_tool": "runtime_tool_alignment_check" if self.status == "registration_request_ready" else "learning_asset_candidate_sandbox_validate",
                "reason": "通过后只生成注册申请证据；是否真实注册/激活仍由 LLM 裁决。",
            },
        }

    def summary_text(self) -> str:
        return (
            "R19 候选包轻量发布门："
            f"status={self.status}；packages={self.package_count}；issues={len(self.issues)}；"
            f"quality={self.quality_gate.get('decision')}；release={self.release_gate.get('decision')}；"
            f"registration_ready={self.registration_request.get('ready')}。{self.summary}"
        )


class LearningAssetReleaseGateBridge:
    """Converts R18 candidate evidence into a minimal LLM-facing registration request."""

    def __init__(self) -> None:
        self._last_report: ReleaseGateReport | None = None

    @property
    def last_report(self) -> ReleaseGateReport | None:
        return self._last_report

    def guide(self) -> dict[str, Any]:
        return build_release_gate_guide()

    def check(self, *, workspace: str | Path, candidate_report: dict[str, Any], notes: str = "") -> ReleaseGateReport:
        guard = WorkspaceGuard(workspace)
        root = guard.resolve_for_artifact(RELEASE_GATE_ROOT)
        root.mkdir(parents=True, exist_ok=True)

        issues: list[ReleaseGateIssue] = []
        packages = [item for item in _as_list(candidate_report.get("packages")) if isinstance(item, dict)]
        source_status = str(candidate_report.get("status") or "empty")
        if source_status != "review_ready":
            issues.append(ReleaseGateIssue("candidate.status", "P1", "R18 候选包必须先达到 review_ready。", source_status))
        if not packages:
            issues.append(ReleaseGateIssue("candidate.packages", "P1", "没有可进入 R19 的候选包。"))
        if not bool(candidate_report.get("static_scan_pass")):
            issues.append(ReleaseGateIssue("candidate.static_scan_pass", "P1", "静态扫描未通过。"))
        if not bool(candidate_report.get("smoke_pass")):
            issues.append(ReleaseGateIssue("candidate.smoke_pass", "P1", "smoke 未通过。"))

        rollback_items: list[dict[str, Any]] = []
        registration_items: list[dict[str, Any]] = []
        for package in packages:
            ref = str(package.get("package_ref") or package.get("asset_ref") or "candidate_package")
            for flag in (
                "candidate_only",
                "writes_real_skill_registry",
                "registers_runtime_tool",
                "activates_skill",
                "releases_tool_handle",
                "invokes_candidate_tool",
                "imports_v1",
                "starts_background_loop",
            ):
                value = package.get(flag)
                if flag == "candidate_only":
                    if value is not True:
                        issues.append(ReleaseGateIssue(f"package.{flag}", "P0", "候选包必须保持 candidate_only=True。", ref))
                elif value is True:
                    issues.append(ReleaseGateIssue(f"package.{flag}", "P0", "候选包越过注册/激活/污染边界。", ref))
            if package.get("status") != "review_ready":
                issues.append(ReleaseGateIssue("package.status", "P1", "候选包必须是 review_ready。", ref))
            if package.get("static_scan_status") != "pass":
                issues.append(ReleaseGateIssue("package.static_scan_status", "P1", "候选包静态扫描必须 pass。", ref))
            if package.get("smoke_status") != "pass":
                issues.append(ReleaseGateIssue("package.smoke_status", "P1", "候选包 smoke 必须 pass。", ref))

            rollback_path = str(package.get("rollback_evidence_path") or "")
            registration_path = str(package.get("registration_review_path") or "")
            rollback_items.append({"package_ref": ref, "path": rollback_path, "present": bool(rollback_path)})
            registration_items.append({"package_ref": ref, "path": registration_path, "present": bool(registration_path)})
            if not rollback_path:
                issues.append(ReleaseGateIssue("rollback_evidence_path", "P1", "缺少 rollback_evidence_path。", ref))
            if not registration_path:
                issues.append(ReleaseGateIssue("registration_review_path", "P1", "缺少 registration_review_path。", ref))

        hard_block = any(issue.severity == "P0" for issue in issues)
        soft_block = any(issue.severity == "P1" for issue in issues)
        quality_ok = not hard_block and not soft_block
        release_ok = quality_ok and source_status == "review_ready" and bool(packages)
        status = "registration_request_ready" if release_ok else "blocked"

        quality_gate = {
            "decision": "pass" if quality_ok else "block",
            "pass": quality_ok,
            "minimal_checks": ["review_ready", "static_scan_pass", "smoke_pass", "candidate_boundary_clean"],
        }
        release_gate = {
            "decision": "pass" if release_ok else "block",
            "allow_release_request": release_ok,
            "allow_activation_now": False,
            "allow_runtime_registration_now": False,
            "reason": "只允许形成注册申请，不允许自动注册/激活。",
        }
        rollback_evidence = {
            "ready": bool(packages) and all(item["present"] for item in rollback_items),
            "items": rollback_items,
            "restore_required_before_activation": True,
        }
        registration_request = {
            "ready": release_ok,
            "request_type": "llm_review_required_before_any_activation",
            "items": registration_items,
            "runtime_registration_allowed_now": False,
            "skill_registry_write_allowed_now": False,
            "tool_handle_release_allowed_now": False,
            "llm_final_decision_required": True,
        }

        report_path = root / "r19_release_gate_request.json"
        report = ReleaseGateReport(
            schema=RELEASE_GATE_SCHEMA,
            generated_at=time(),
            status=status,
            summary=(
                "轻量四项门已完成：质量门、发布门、回滚证据、注册申请。"
                if release_ok else
                "轻量四项门发现阻断项，请回到 R18 validate/review 修复证据。"
            ),
            workspace_root=str(guard.workspace),
            report_path=str(report_path),
            source_candidate_status=source_status,
            package_count=len(packages),
            quality_gate=quality_gate,
            release_gate=release_gate,
            rollback_evidence=rollback_evidence,
            registration_request=registration_request,
            issues=issues,
            chain=build_release_gate_guide()["canonical_pipeline"],
        )
        try:
            report_path.write_text(json.dumps(report.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        except (OSError, WorkspaceViolation) as exc:
            issues = list(issues) + [ReleaseGateIssue("report_path", "P1", f"R19 报告写入失败：{exc}", str(report_path))]
            report = ReleaseGateReport(
                schema=report.schema,
                generated_at=report.generated_at,
                status="blocked",
                summary="R19 报告写入失败，请检查 workspace。",
                workspace_root=report.workspace_root,
                report_path=str(report_path),
                source_candidate_status=source_status,
                package_count=len(packages),
                quality_gate={**quality_gate, "decision": "block", "pass": False},
                release_gate={**release_gate, "decision": "block", "allow_release_request": False},
                rollback_evidence=rollback_evidence,
                registration_request={**registration_request, "ready": False},
                issues=issues,
                chain=build_release_gate_guide()["canonical_pipeline"],
            )
        self._last_report = report
        return report

    def public_dict(self) -> dict[str, Any]:
        if self._last_report is None:
            return {"schema": RELEASE_GATE_SCHEMA, "status": "empty", "message": "暂无 R19 发布门报告。"}
        return self._last_report.public_dict()

    def build_planner_hint(self) -> str:
        if self._last_report is None:
            return ""
        return (
            f"最近 R19 候选发布门：status={self._last_report.status}; "
            f"packages={self._last_report.package_count}; registration_ready={self._last_report.registration_request.get('ready')}"
        )


def build_release_gate_guide() -> dict[str, Any]:
    return {
        "schema": RELEASE_GATE_SCHEMA,
        "purpose": "R19 轻量执行版：把 R18 候选包证据压成质量门、发布门、回滚证据、注册申请四项结果。",
        "commands": {
            "guide": "asset-release guide",
            "gate": "asset-release gate",
            "drill": "asset-release drill pytest missing tests",
        },
        "canonical_pipeline": [
            "learning_asset_candidate_sandbox_build",
            "learning_asset_candidate_sandbox_validate",
            "learning_asset_candidate_sandbox_review",
            "learning_asset_release_gate_check",
        ],
        "execution_first_policy": {
            "keep": ["quality_gate", "release_gate", "rollback_evidence", "registration_request"],
            "remove": ["complex scoring", "multi-level approval", "auto activation"],
            "final_decider": "LLM",
        },
        "hard_boundaries": {
            "may_write": [".linyuanzhe/candidate_sandbox/r19/r19_release_gate_request.json"],
            "must_not": [
                "write real Skill registry",
                "register Runtime tools",
                "activate Skill",
                "release tool handle",
                "invoke candidate tool",
                "import/copy v1",
                "call model/provider/network/shell",
                "start background loop",
            ],
        },
    }


def build_learning_asset_release_gate_guide_adapter():
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary="R19 轻量发布门指南已生成：四项直检，LLM 裁决，不自动注册/激活。",
            data=build_release_gate_guide(),
        )

    return adapter


def build_learning_asset_release_gate_check_adapter(bridge: LearningAssetReleaseGateBridge, candidate_sandbox: Any):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        candidate_report = candidate_sandbox.public_dict() if hasattr(candidate_sandbox, "public_dict") else {}
        try:
            report = bridge.check(
                workspace=context.workspace,
                candidate_report=candidate_report,
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
            )
        except (TypeError, ValueError, OSError) as exc:
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.FAILED,
                f"R19 轻量发布门失败：{exc}",
                error_code="learning_asset_release_gate_failed",
            )
        status = ToolResultStatus.OK if report.status == "registration_request_ready" else ToolResultStatus.FAILED
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=status,
            output_summary=report.summary_text(),
            data=report.public_dict(),
            artifacts=[report.report_path] if report.report_path else [],
            error_code="" if status is ToolResultStatus.OK else "learning_asset_release_gate_blocked",
        )

    return adapter


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]
