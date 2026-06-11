"""L6.70.2-R18 Tool/Skill candidate package production sandbox.

R17 binds future Tool/Skill contracts to the existing L6.22 sandbox preflight
chain.  R18 is the next governed step: it materializes reviewable candidate
packages inside an isolated workspace folder, runs deterministic static/smoke
checks, records rollback evidence, and prepares a registration review envelope.

Boundary: this module may write *candidate package files* only under
``.linyuanzhe/candidate_sandbox/r18`` in the current governed workspace.  It
never writes the real Skill registry, never registers Runtime tools, never
releases tool handles, never imports/copies v1, never invokes candidate tools,
never calls models, never touches network/shell, and never starts loops.  LLM
remains the final decider for any future activation.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import Any

from tiangong_agent_shell.safe_logging import redact_text

from .tool_invocation import ToolInvocation
from .tool_result import ToolResult, ToolResultStatus
from .turn_context import TurnContext
from .workspace_guard import WorkspaceGuard, WorkspaceViolation
from .learning_asset_adapter import ADAPTER_SCHEMA, infer_adapter_template_id, render_candidate_adapter_code

CANDIDATE_SANDBOX_SCHEMA = "tiangong.l6702.r18.learning_asset_candidate_sandbox.v1"
CANDIDATE_SANDBOX_PROFILE = "isolated_workspace_candidate_package_only"
CANDIDATE_SANDBOX_ROOT = ".linyuanzhe/candidate_sandbox/r18"
CANDIDATE_SANDBOX_TOOL_NAMES = {
    "learning_asset_candidate_sandbox_guide",
    "learning_asset_candidate_sandbox_build",
    "learning_asset_candidate_sandbox_validate",
    "learning_asset_candidate_sandbox_review",
}

SENSITIVE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer|token|secret|password|credential)\s*[:=]\s*[^\s,;]+"
)
FORBIDDEN_TEXT_PATTERNS = {
    "v1_import": re.compile(r"(?i)\b(from|import)\s+v1\b"),
    "subprocess": re.compile(r"(?i)\bsubprocess\b"),
    "os_system": re.compile(r"(?i)\bos\.system\s*\("),
    "eval": re.compile(r"(?i)\beval\s*\("),
    "exec": re.compile(r"(?i)\bexec\s*\("),
    "socket": re.compile(r"(?i)\bsocket\b"),
    "requests": re.compile(r"(?i)\brequests\b"),
    "urllib": re.compile(r"(?i)\burllib\b"),
    "monkey_patch_affirmative": re.compile(r"(?i)monkey\s*patch\s*(=|:)\s*true"),
    "background_loop_affirmative": re.compile(r"(?i)background\s*loop\s*(=|:)\s*true"),
    "credential_assignment": SENSITIVE_PATTERN,
}


@dataclass(frozen=True)
class CandidateSandboxIssue:
    field: str
    severity: str
    message: str
    ref: str = ""

    def public_dict(self) -> dict[str, str]:
        return {"field": self.field, "severity": self.severity, "message": self.message, "ref": self.ref}


@dataclass(frozen=True)
class CandidatePackageRecord:
    package_ref: str
    asset_ref: str
    asset_kind: str
    name: str
    status: str
    package_dir: str
    zip_path: str
    manifest_path: str
    files: list[str]
    static_scan_status: str
    smoke_status: str
    rollback_evidence_path: str
    registration_review_path: str
    aligned_sandbox_ref: str = ""
    candidate_only: bool = True
    writes_real_skill_registry: bool = False
    registers_runtime_tool: bool = False
    activates_skill: bool = False
    releases_tool_handle: bool = False
    invokes_candidate_tool: bool = False
    imports_v1: bool = False
    starts_background_loop: bool = False

    def __post_init__(self) -> None:
        if not self.candidate_only:
            raise ValueError("R18 candidate package must remain candidate-only")
        if any((
            self.writes_real_skill_registry,
            self.registers_runtime_tool,
            self.activates_skill,
            self.releases_tool_handle,
            self.invokes_candidate_tool,
            self.imports_v1,
            self.starts_background_loop,
        )):
            raise ValueError("R18 candidate package crossed activation/registration/pollution boundary")

    def public_dict(self) -> dict[str, Any]:
        return {
            "package_ref": self.package_ref,
            "asset_ref": self.asset_ref,
            "asset_kind": self.asset_kind,
            "name": self.name,
            "status": self.status,
            "package_dir": self.package_dir,
            "zip_path": self.zip_path,
            "manifest_path": self.manifest_path,
            "files": list(self.files),
            "static_scan_status": self.static_scan_status,
            "smoke_status": self.smoke_status,
            "rollback_evidence_path": self.rollback_evidence_path,
            "registration_review_path": self.registration_review_path,
            "aligned_sandbox_ref": self.aligned_sandbox_ref,
            "candidate_only": self.candidate_only,
            "writes_real_skill_registry": self.writes_real_skill_registry,
            "registers_runtime_tool": self.registers_runtime_tool,
            "activates_skill": self.activates_skill,
            "releases_tool_handle": self.releases_tool_handle,
            "invokes_candidate_tool": self.invokes_candidate_tool,
            "imports_v1": self.imports_v1,
            "starts_background_loop": self.starts_background_loop,
        }


@dataclass(frozen=True)
class CandidateSandboxReport:
    schema: str
    generated_at: float
    status: str
    summary: str
    sandbox_profile: str
    workspace_root: str
    package_root: str
    packages: list[CandidatePackageRecord] = field(default_factory=list)
    issues: list[CandidateSandboxIssue] = field(default_factory=list)
    chain: list[str] = field(default_factory=list)
    candidate_only: bool = True
    writes_candidate_files: bool = True
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
        if not self.candidate_only:
            raise ValueError("R18 report must remain candidate-only")
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
            raise ValueError("R18 report crossed registry/activation/pollution boundary")

    @property
    def package_count(self) -> int:
        return len(self.packages)

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "status": self.status,
            "summary": self.summary,
            "sandbox_profile": self.sandbox_profile,
            "workspace_root": self.workspace_root,
            "package_root": self.package_root,
            "package_count": len(self.packages),
            "tool_package_count": sum(1 for item in self.packages if item.asset_kind == "tool"),
            "skill_package_count": sum(1 for item in self.packages if item.asset_kind == "skill"),
            "static_scan_pass": all(item.static_scan_status == "pass" for item in self.packages) and not any(issue.severity in {"P0", "P1"} for issue in self.issues),
            "smoke_pass": all(item.smoke_status == "pass" for item in self.packages),
            "review_ready_count": sum(1 for item in self.packages if item.status == "review_ready"),
            "packages": [item.public_dict() for item in self.packages],
            "issues": [item.public_dict() for item in self.issues],
            "issue_count": len(self.issues),
            "chain": list(self.chain),
            "candidate_only": self.candidate_only,
            "writes_candidate_files": self.writes_candidate_files,
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
                "next_tool": "learning_asset_candidate_sandbox_review" if self.status in {"pass", "review_ready"} else "learning_asset_candidate_sandbox_validate",
                "reason": "候选包通过静态/smoke 后进入注册审阅；仍不得自动注册或激活。",
            },
        }

    def summary_text(self) -> str:
        return (
            "R18 Tool/Skill 候选包生产沙箱："
            f"status={self.status}；packages={len(self.packages)}；issues={len(self.issues)}；"
            f"candidate_only={self.candidate_only}。{self.summary}"
        )


class LearningAssetCandidateSandboxBridge:
    """Produces and validates isolated candidate packages for future Tool/Skill assets."""

    def __init__(self) -> None:
        self._last_report: CandidateSandboxReport | None = None

    @property
    def last_report(self) -> CandidateSandboxReport | None:
        return self._last_report

    def guide(self) -> dict[str, Any]:
        return build_candidate_sandbox_guide()

    def build(
        self,
        *,
        workspace: str | Path,
        learning_contract_report: dict[str, Any],
        sandbox_alignment_report: dict[str, Any],
        notes: str = "",
        max_items: int = 12,
    ) -> CandidateSandboxReport:
        guard = WorkspaceGuard(workspace)
        root = guard.resolve_for_artifact(CANDIDATE_SANDBOX_ROOT)
        root.mkdir(parents=True, exist_ok=True)
        contracts = _select_contracts(learning_contract_report, max_items=max_items)
        issues: list[CandidateSandboxIssue] = []
        mappings = _mapping_by_asset_ref(sandbox_alignment_report)
        packages: list[CandidatePackageRecord] = []

        if not contracts:
            issues.append(CandidateSandboxIssue("contracts", "P1", "没有可生产候选包的 Tool/Skill 统一资产契约。"))

        for contract in contracts:
            kind = _safe_text(contract.get("asset_kind"), limit=40)
            asset_ref = _safe_text(contract.get("asset_ref"), limit=220)
            if kind == "tool" and not mappings.get(asset_ref, {}).get("aligned", False):
                issues.append(CandidateSandboxIssue("sandbox_alignment", "P1", "Tool 契约未通过 R17 沙箱前置映射，拒绝生成候选包。", asset_ref))
                continue
            try:
                record, record_issues = _materialize_candidate_package(
                    guard=guard,
                    root=root,
                    contract=contract,
                    mapping=mappings.get(asset_ref, {}),
                    notes=notes,
                )
                packages.append(record)
                issues.extend(record_issues)
            except (OSError, WorkspaceViolation, ValueError) as exc:
                issues.append(CandidateSandboxIssue("package_materialize", "P1", f"候选包生成失败：{exc}", asset_ref))

        status = _status(packages, issues)
        report = CandidateSandboxReport(
            schema=CANDIDATE_SANDBOX_SCHEMA,
            generated_at=time(),
            status=status,
            summary=_summary(packages=packages, issues=issues, notes=notes),
            sandbox_profile=CANDIDATE_SANDBOX_PROFILE,
            workspace_root=str(guard.workspace),
            package_root=str(root),
            packages=packages,
            issues=issues,
            chain=build_candidate_sandbox_guide()["canonical_pipeline"],
        )
        self._last_report = report
        return report

    def validate(self, *, workspace: str | Path, notes: str = "") -> CandidateSandboxReport:
        if self._last_report is None:
            guard = WorkspaceGuard(workspace)
            root = guard.resolve_for_artifact(CANDIDATE_SANDBOX_ROOT)
            report = CandidateSandboxReport(
                schema=CANDIDATE_SANDBOX_SCHEMA,
                generated_at=time(),
                status="empty",
                summary="暂无 R18 候选包报告，请先执行 learning_asset_candidate_sandbox_build。",
                sandbox_profile=CANDIDATE_SANDBOX_PROFILE,
                workspace_root=str(guard.workspace),
                package_root=str(root),
                packages=[],
                issues=[CandidateSandboxIssue("last_report", "P1", "暂无候选包可校验。")],
                chain=build_candidate_sandbox_guide()["canonical_pipeline"],
            )
            self._last_report = report
            return report

        guard = WorkspaceGuard(workspace)
        issues: list[CandidateSandboxIssue] = []
        refreshed: list[CandidatePackageRecord] = []
        for package in self._last_report.packages:
            try:
                record, record_issues = _scan_existing_package(guard, package)
                refreshed.append(record)
                issues.extend(record_issues)
            except (OSError, WorkspaceViolation, ValueError) as exc:
                issues.append(CandidateSandboxIssue("package_validate", "P1", f"候选包复核失败：{exc}", package.package_ref))
                refreshed.append(package)
        status = _status(refreshed, issues)
        report = CandidateSandboxReport(
            schema=CANDIDATE_SANDBOX_SCHEMA,
            generated_at=time(),
            status=status,
            summary=_summary(packages=refreshed, issues=issues, notes=notes),
            sandbox_profile=CANDIDATE_SANDBOX_PROFILE,
            workspace_root=str(guard.workspace),
            package_root=self._last_report.package_root,
            packages=refreshed,
            issues=issues,
            chain=build_candidate_sandbox_guide()["canonical_pipeline"],
        )
        self._last_report = report
        return report

    def review(self, *, workspace: str | Path, notes: str = "") -> CandidateSandboxReport:
        report = self.validate(workspace=workspace, notes=notes)
        # Review does not mutate files or registries; it just tightens the public
        # status summary for LLM decision making.
        status = "review_ready" if report.status == "pass" and report.packages else report.status
        reviewed = CandidateSandboxReport(
            schema=report.schema,
            generated_at=time(),
            status=status,
            summary=(
                report.summary
                + " 注册审阅结论：仅允许 LLM 查看 manifest/scan/smoke/rollback 证据后决定是否进入后续质量门；当前不注册、不激活。"
            ),
            sandbox_profile=report.sandbox_profile,
            workspace_root=report.workspace_root,
            package_root=report.package_root,
            packages=report.packages,
            issues=report.issues,
            chain=report.chain,
        )
        self._last_report = reviewed
        return reviewed

    def public_dict(self) -> dict[str, Any]:
        if self._last_report is None:
            return {"schema": CANDIDATE_SANDBOX_SCHEMA, "status": "empty", "message": "暂无 R18 候选包沙箱报告。"}
        return self._last_report.public_dict()

    def build_planner_hint(self) -> str:
        if self._last_report is None:
            return ""
        return (
            f"最近 R18 候选包沙箱：status={self._last_report.status}; "
            f"packages={len(self._last_report.packages)}; candidate_only=True; registration_review_required=True"
        )


def build_candidate_sandbox_guide() -> dict[str, Any]:
    return {
        "schema": CANDIDATE_SANDBOX_SCHEMA,
        "profile": CANDIDATE_SANDBOX_PROFILE,
        "purpose": "把 R16/R17 已通过的 Tool/Skill 候选真实落盘为隔离候选包，并完成静态扫描、smoke、回滚证据和注册审阅。",
        "commands": {
            "guide": "asset-candidate-sandbox guide",
            "build": "asset-candidate-sandbox build pytest missing tests",
            "validate": "asset-candidate-sandbox validate",
            "review": "asset-candidate-sandbox review",
            "drill": "asset-candidate-sandbox drill pytest missing tests",
        },
        "canonical_pipeline": [
            "synthesize_experience_candidates",
            "queue_skill_candidates",
            "queue_tool_production_requests",
            "learning_asset_contract_normalize",
            "learning_asset_contract_validate",
            "learning_asset_sandbox_align",
            "learning_asset_sandbox_validate",
            "learning_asset_candidate_sandbox_build",
            "learning_asset_candidate_sandbox_validate",
            "learning_asset_candidate_sandbox_review",
        ],
        "hard_boundaries": {
            "may_write": ["isolated candidate package files under .linyuanzhe/candidate_sandbox/r18"],
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
            "llm_policy": "LLM 是主脑；R18 只交付证据包与 next_action_hint，不自动发布或激活。",
        },
    }


def build_learning_asset_candidate_sandbox_guide_adapter():
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary="R18 候选包生产沙箱指南已生成：只落盘隔离候选包、扫描、smoke、留回滚证据，不注册不激活。",
            data=build_candidate_sandbox_guide(),
        )

    return adapter


def build_learning_asset_candidate_sandbox_build_adapter(bridge: LearningAssetCandidateSandboxBridge, learning_contract: Any, sandbox_alignment: Any):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            report = bridge.build(
                workspace=context.workspace,
                learning_contract_report=learning_contract.public_dict(),
                sandbox_alignment_report=sandbox_alignment.public_dict(),
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
                max_items=int(invocation.arguments.get("max_items") or 12),
            )
        except (TypeError, ValueError, OSError) as exc:
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.FAILED,
                f"R18 候选包生成失败：{exc}",
                error_code="learning_asset_candidate_sandbox_build_failed",
            )
        status = ToolResultStatus.OK if report.status in {"pass", "review_ready"} else ToolResultStatus.FAILED
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=status,
            output_summary=report.summary_text(),
            data=report.public_dict(),
            artifacts=[item.package_dir for item in report.packages] + [item.zip_path for item in report.packages],
            error_code="" if status is ToolResultStatus.OK else "learning_asset_candidate_sandbox_build_needs_review",
        )

    return adapter


def build_learning_asset_candidate_sandbox_validate_adapter(bridge: LearningAssetCandidateSandboxBridge):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            report = bridge.validate(
                workspace=context.workspace,
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
            )
        except (TypeError, ValueError, OSError) as exc:
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.FAILED,
                f"R18 候选包校验失败：{exc}",
                error_code="learning_asset_candidate_sandbox_validate_failed",
            )
        status = ToolResultStatus.OK if report.status == "pass" else ToolResultStatus.FAILED
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=status,
            output_summary=report.summary_text(),
            data=report.public_dict(),
            artifacts=[item.package_dir for item in report.packages] + [item.zip_path for item in report.packages],
            error_code="" if status is ToolResultStatus.OK else "learning_asset_candidate_sandbox_validate_needs_review",
        )

    return adapter


def build_learning_asset_candidate_sandbox_review_adapter(bridge: LearningAssetCandidateSandboxBridge):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            report = bridge.review(
                workspace=context.workspace,
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
            )
        except (TypeError, ValueError, OSError) as exc:
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.FAILED,
                f"R18 候选包注册审阅失败：{exc}",
                error_code="learning_asset_candidate_sandbox_review_failed",
            )
        status = ToolResultStatus.OK if report.status == "review_ready" else ToolResultStatus.FAILED
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=status,
            output_summary=report.summary_text(),
            data=report.public_dict(),
            artifacts=[item.package_dir for item in report.packages] + [item.zip_path for item in report.packages],
            error_code="" if status is ToolResultStatus.OK else "learning_asset_candidate_sandbox_review_needs_review",
        )

    return adapter


def _select_contracts(report: dict[str, Any], *, max_items: int) -> list[dict[str, Any]]:
    contracts = [item for item in _as_list(report.get("contracts")) if isinstance(item, dict)]
    selected = [item for item in contracts if item.get("asset_kind") in {"tool", "skill"}]
    return selected[: max(1, min(int(max_items), 50))]


def _mapping_by_asset_ref(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mappings: dict[str, dict[str, Any]] = {}
    for item in _as_list(report.get("mappings")):
        if isinstance(item, dict):
            asset_ref = _safe_text(item.get("asset_ref"), limit=220)
            if asset_ref:
                mappings[asset_ref] = item
    return mappings


def _materialize_candidate_package(
    *,
    guard: WorkspaceGuard,
    root: Path,
    contract: dict[str, Any],
    mapping: dict[str, Any],
    notes: str,
) -> tuple[CandidatePackageRecord, list[CandidateSandboxIssue]]:
    kind = _safe_text(contract.get("asset_kind"), limit=40)
    asset_ref = _safe_text(contract.get("asset_ref"), limit=220)
    name = _slug_name(contract.get("name") or contract.get("usage_card", {}).get("title") or kind or "candidate")
    package_ref = _ref("candidate_package", asset_ref, kind, name)
    package_dir = guard.resolve_for_artifact(root / f"{kind}_{name}_{package_ref.split(':')[-1]}")
    package_dir.mkdir(parents=True, exist_ok=True)

    manifest = _build_manifest(contract=contract, mapping=mapping, package_ref=package_ref, notes=notes)
    files: dict[str, str] = {
        "manifest.json": json.dumps(manifest, ensure_ascii=False, indent=2),
        "rollback_evidence.json": json.dumps(_build_rollback(package_ref, contract), ensure_ascii=False, indent=2),
        "registration_review.json": json.dumps(_build_registration_review(package_ref, contract), ensure_ascii=False, indent=2),
        "README.md": _render_readme(contract, manifest),
    }
    if kind == "tool":
        files["tool_adapter_draft.py"] = _render_tool_adapter_draft(contract)
        files["tests/test_static_contract.py"] = _render_tool_static_test(contract)
    elif kind == "skill":
        files["SKILL.md"] = _render_skill_draft(contract)
        files["tests/test_skill_contract.md"] = _render_skill_static_test(contract)
    else:
        raise ValueError(f"unsupported candidate package kind: {kind}")

    written: list[str] = []
    for rel, content in files.items():
        target = guard.resolve_for_write(package_dir / rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written.append(str(target))

    scan_status, smoke_status, issues = _scan_package(package_dir)
    (package_dir / "static_scan.json").write_text(json.dumps({"status": scan_status, "issues": [i.public_dict() for i in issues]}, ensure_ascii=False, indent=2), encoding="utf-8")
    (package_dir / "smoke_result.json").write_text(json.dumps({"status": smoke_status, "kind": kind}, ensure_ascii=False, indent=2), encoding="utf-8")
    written.extend([str(package_dir / "static_scan.json"), str(package_dir / "smoke_result.json")])
    zip_path = _zip_package(package_dir)
    written.append(str(zip_path))

    status = "review_ready" if scan_status == "pass" and smoke_status == "pass" and not any(i.severity in {"P0", "P1"} for i in issues) else "needs_review"
    record = CandidatePackageRecord(
        package_ref=package_ref,
        asset_ref=asset_ref,
        asset_kind=kind,
        name=name,
        status=status,
        package_dir=str(package_dir),
        zip_path=str(zip_path),
        manifest_path=str(package_dir / "manifest.json"),
        files=written,
        static_scan_status=scan_status,
        smoke_status=smoke_status,
        rollback_evidence_path=str(package_dir / "rollback_evidence.json"),
        registration_review_path=str(package_dir / "registration_review.json"),
        aligned_sandbox_ref=_safe_text(mapping.get("sandbox_validation_ref"), limit=220),
    )
    return record, issues


def _scan_existing_package(guard: WorkspaceGuard, package: CandidatePackageRecord) -> tuple[CandidatePackageRecord, list[CandidateSandboxIssue]]:
    package_dir = guard.resolve_for_read(package.package_dir)
    scan_status, smoke_status, issues = _scan_package(package_dir)
    status = "review_ready" if scan_status == "pass" and smoke_status == "pass" and not any(i.severity in {"P0", "P1"} for i in issues) else "needs_review"
    refreshed = CandidatePackageRecord(
        package_ref=package.package_ref,
        asset_ref=package.asset_ref,
        asset_kind=package.asset_kind,
        name=package.name,
        status=status,
        package_dir=package.package_dir,
        zip_path=package.zip_path,
        manifest_path=package.manifest_path,
        files=package.files,
        static_scan_status=scan_status,
        smoke_status=smoke_status,
        rollback_evidence_path=package.rollback_evidence_path,
        registration_review_path=package.registration_review_path,
        aligned_sandbox_ref=package.aligned_sandbox_ref,
    )
    return refreshed, issues


def _scan_package(package_dir: Path) -> tuple[str, str, list[CandidateSandboxIssue]]:
    issues: list[CandidateSandboxIssue] = []
    manifest_path = package_dir / "manifest.json"
    if not manifest_path.exists():
        issues.append(CandidateSandboxIssue("manifest", "P0", "候选包缺少 manifest.json。", str(package_dir)))
        return "fail", "fail", issues
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(CandidateSandboxIssue("manifest", "P0", f"manifest JSON 解析失败：{exc}", str(manifest_path)))
        return "fail", "fail", issues
    for key in (
        "candidate_only",
        "review_before_activation",
        "no_real_skill_registry_write",
        "no_runtime_tool_registration",
        "no_skill_activation",
        "no_tool_handle_release",
        "no_candidate_tool_invocation",
        "no_model_dispatch",
        "no_network",
        "no_shell",
        "no_background_loop",
        "no_v1_import_or_source_copy",
    ):
        if manifest.get(key) is not True:
            issues.append(CandidateSandboxIssue(f"manifest.{key}", "P0", "候选包安全边界字段必须为 True。", str(manifest_path)))
    files = [path for path in package_dir.rglob("*") if path.is_file() and path.name != "candidate_package.zip"]
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for code, pattern in FORBIDDEN_TEXT_PATTERNS.items():
            if pattern.search(text):
                issues.append(CandidateSandboxIssue("static_scan", "P0", f"命中禁止模式：{code}", str(path)))
    asset_kind = _safe_text(manifest.get("asset_kind"), limit=40)
    smoke_ok = False
    if asset_kind == "tool":
        draft = package_dir / "tool_adapter_draft.py"
        if not draft.exists():
            issues.append(CandidateSandboxIssue("tool_adapter_draft", "P0", "Tool 候选缺少 tool_adapter_draft.py。", str(package_dir)))
        else:
            source = draft.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source, filename=str(draft))
                function_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
                smoke_ok = "candidate_adapter_draft" in function_names and "candidate_tool_main" not in function_names
                if not smoke_ok:
                    issues.append(CandidateSandboxIssue("tool_adapter_draft", "P1", "Tool 候选草案必须只暴露 candidate_adapter_draft，不能暴露可执行 main。", str(draft)))
            except SyntaxError as exc:
                issues.append(CandidateSandboxIssue("tool_adapter_draft", "P0", f"Python 草案语法失败：{exc}", str(draft)))
    elif asset_kind == "skill":
        skill = package_dir / "SKILL.md"
        if not skill.exists():
            issues.append(CandidateSandboxIssue("skill_draft", "P0", "Skill 候选缺少 SKILL.md。", str(package_dir)))
        else:
            text = skill.read_text(encoding="utf-8", errors="ignore")
            smoke_ok = "# " in text and "候选" in text and "不得" in text
            if not smoke_ok:
                issues.append(CandidateSandboxIssue("skill_draft", "P1", "Skill 草案缺少候选/禁用边界说明。", str(skill)))
    else:
        issues.append(CandidateSandboxIssue("asset_kind", "P0", f"不支持的候选包类型：{asset_kind}", str(manifest_path)))

    scan_status = "pass" if not any(issue.severity == "P0" for issue in issues) else "fail"
    smoke_status = "pass" if smoke_ok and not any(issue.severity in {"P0", "P1"} for issue in issues) else "fail"
    return scan_status, smoke_status, issues


def _build_manifest(*, contract: dict[str, Any], mapping: dict[str, Any], package_ref: str, notes: str) -> dict[str, Any]:
    return {
        "schema": CANDIDATE_SANDBOX_SCHEMA,
        "package_ref": package_ref,
        "asset_ref": _safe_text(contract.get("asset_ref"), limit=220),
        "asset_kind": _safe_text(contract.get("asset_kind"), limit=40),
        "namespace": _safe_text(contract.get("namespace"), limit=160),
        "name": _safe_text(contract.get("name"), limit=160),
        "version": _safe_text(contract.get("version"), limit=80) or "0.1.0-candidate",
        "purpose": _safe_text(contract.get("purpose"), limit=700),
        "adapter_template_schema": ADAPTER_SCHEMA,
        "adapter_template_id": infer_adapter_template_id(contract.get("name"), contract.get("purpose"), contract.get("usage_card"), notes),
        "source_trace": contract.get("source_trace") if isinstance(contract.get("source_trace"), dict) else {},
        "usage_card": contract.get("usage_card") if isinstance(contract.get("usage_card"), dict) else {},
        "chain_recipe": _as_list(contract.get("chain_recipe"))[:20],
        "validation_contract": contract.get("validation_contract") if isinstance(contract.get("validation_contract"), dict) else {},
        "rollback_contract": contract.get("rollback_contract") if isinstance(contract.get("rollback_contract"), dict) else {},
        "audit_contract": contract.get("audit_contract") if isinstance(contract.get("audit_contract"), dict) else {},
        "runtime_binding": contract.get("runtime_binding") if isinstance(contract.get("runtime_binding"), dict) else {},
        "aligned_sandbox_mapping": mapping,
        "notes": _safe_text(notes, limit=400),
        "sandbox_profile": CANDIDATE_SANDBOX_PROFILE,
        "candidate_only": True,
        "review_before_activation": True,
        "no_real_skill_registry_write": True,
        "no_runtime_tool_registration": True,
        "no_skill_activation": True,
        "no_tool_handle_release": True,
        "no_candidate_tool_invocation": True,
        "no_model_dispatch": True,
        "no_network": True,
        "no_shell": True,
        "no_background_loop": True,
        "no_v1_import_or_source_copy": True,
        "llm_is_final_decider": True,
    }


def _build_rollback(package_ref: str, contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "package_ref": package_ref,
        "asset_ref": _safe_text(contract.get("asset_ref"), limit=220),
        "strategy": "candidate package can be deleted or requeued; no Runtime registry or Skill registry rollback is needed because nothing was activated.",
        "delete_scope": "this candidate package directory only",
        "checkpoint_required_before_future_activation": True,
        "restore_required_before_future_activation": True,
    }


def _build_registration_review(package_ref: str, contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "package_ref": package_ref,
        "asset_ref": _safe_text(contract.get("asset_ref"), limit=220),
        "asset_kind": _safe_text(contract.get("asset_kind"), limit=40),
        "proposed_name": _slug_name(contract.get("name") or "candidate"),
        "review_status": "pending_llm_decision",
        "required_before_activation": [
            "static_scan_pass",
            "smoke_pass",
            "quality_gate_pass",
            "release_gate_pass",
            "rollback_checkpoint",
            "audit_manifest",
            "explicit_llm_decision",
        ],
        "activation_allowed_now": False,
        "runtime_registration_allowed_now": False,
        "skill_registry_write_allowed_now": False,
    }


def _render_tool_adapter_draft(contract: dict[str, Any]) -> str:
    """Render a practical R21-safe adapter draft for future R20 activation."""
    template_id = infer_adapter_template_id(
        contract.get("name"),
        contract.get("purpose"),
        contract.get("usage_card"),
    )
    return render_candidate_adapter_code(template_id)


def _render_tool_static_test(contract: dict[str, Any]) -> str:
    asset_ref = _safe_text(contract.get("asset_ref"), limit=220)
    return (
        "def test_r18_tool_candidate_static_contract():\n"
        f"    asset_ref = {asset_ref!r}\n"
        "    assert asset_ref\n"
        "    assert True  # candidate_adapter_draft AST and no-side-effect boundaries are scanned by Runtime.\n"
    )


def _render_skill_draft(contract: dict[str, Any]) -> str:
    name = _safe_text(contract.get("name"), limit=160) or "candidate_skill"
    purpose = _safe_text(contract.get("purpose"), limit=900)
    usage = contract.get("usage_card") if isinstance(contract.get("usage_card"), dict) else {}
    chain = [str(item) for item in _as_list(contract.get("chain_recipe"))[:12]]
    lines = [
        f"# {name} 候选 Skill 草案",
        "",
        "## 状态",
        "",
        "候选。不得写入正式 Skill 注册表，不得激活，不得释放能力句柄。",
        "",
        "## 用途",
        "",
        purpose or "待审阅 Skill 用途。",
        "",
        "## 触发规则",
        "",
        f"- {usage.get('when_to_use') or '由 LLM 根据任务目标和 Runtime 证据判断。'}",
        "",
        "## 使用链路",
        "",
    ]
    lines.extend(f"- {item}" for item in (chain or ["read evidence", "select governed Runtime tools", "validate", "handoff"]))
    lines.extend([
        "",
        "## 禁止边界",
        "",
        "- 不得自动注册或激活。",
        "- 不得绕过质量门、发布门、回滚证据和审计。",
        "- 不得导入或复制 v1 源码。",
        "- 不得调用模型、网络、shell 或候选工具。",
    ])
    return "\n".join(lines) + "\n"


def _render_skill_static_test(contract: dict[str, Any]) -> str:
    return (
        "# R18 Skill candidate static smoke\n\n"
        "- SKILL.md must contain candidate status and forbidden boundaries\n"
        "- real skill registry write is forbidden\n"
        f"- asset_ref: `{_safe_text(contract.get('asset_ref'), limit=220)}`\n"
    )


def _render_readme(contract: dict[str, Any], manifest: dict[str, Any]) -> str:
    return (
        f"# R18 Candidate Package: {_safe_text(contract.get('name'), limit=120)}\n\n"
        f"- asset_kind: `{manifest['asset_kind']}`\n"
        f"- asset_ref: `{manifest['asset_ref']}`\n"
        f"- sandbox_profile: `{CANDIDATE_SANDBOX_PROFILE}`\n"
        "- status: candidate package only; review required before activation\n\n"
        "This package is evidence for LLM review. It is not a registered Runtime tool or active Skill.\n"
    )


def _zip_package(package_dir: Path) -> Path:
    zip_path = package_dir / "candidate_package.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(package_dir.rglob("*")):
            if path.is_file() and path != zip_path:
                zf.write(path, path.relative_to(package_dir).as_posix())
    return zip_path


def _status(packages: list[CandidatePackageRecord], issues: list[CandidateSandboxIssue]) -> str:
    if not packages:
        return "empty" if not issues else "needs_review"
    if any(issue.severity in {"P0", "P1"} for issue in issues):
        return "needs_review"
    if all(item.static_scan_status == "pass" and item.smoke_status == "pass" for item in packages):
        return "pass"
    return "needs_review"


def _summary(*, packages: list[CandidatePackageRecord], issues: list[CandidateSandboxIssue], notes: str) -> str:
    note_hint = "；已接收人工备注" if _safe_text(notes, limit=120) else ""
    if not packages:
        return f"未生成候选包；issues={len(issues)}{note_hint}。"
    return (
        "已在隔离 workspace 生成 Tool/Skill 候选包，并完成静态扫描、smoke、回滚证据和注册审阅文件；"
        f"packages={len(packages)}；tool={sum(1 for item in packages if item.asset_kind == 'tool')}；"
        f"skill={sum(1 for item in packages if item.asset_kind == 'skill')}；issues={len(issues)}{note_hint}。"
    )


def _slug_name(value: Any) -> str:
    text = _safe_text(value, limit=120).lower()
    text = re.sub(r"[^a-z0-9_\u4e00-\u9fff-]+", "_", text).strip("_")
    return text[:80] or "candidate"


def _safe_text(value: Any, *, limit: int = 700) -> str:
    text = redact_text(str(value or ""))
    text = SENSITIVE_PATTERN.sub(lambda m: f"{m.group(1)}=<redacted>", text)
    return text.strip()[:limit]


def _ref(prefix: str, *parts: Any) -> str:
    material = "|".join(_safe_text(part, limit=500) for part in parts)
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}:r18_{digest}"


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value in (None, ""):
        return []
    return [value]
