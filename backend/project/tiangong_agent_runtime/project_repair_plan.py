"""L6.25 项目雷达与工程修复外壳闭环。

该模块只在 Runtime 外壳层把现有项目雷达、工程诊断、质量检查摘要压缩为
PatchPlan / RegressionHint / RollbackEvidence，供 LLM 后续按最小变更执行。
它不应用补丁、不写文件、不注册工具、不激活 Skill、不修改 tiangong_kernel。
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import Any, Iterable

from tiangong_agent_shell.safe_logging import redact_text

from .project_index_bridge import ProjectIndexSnapshot
from .tool_invocation import ToolInvocation
from .tool_result import ToolResult, ToolResultStatus
from .turn_context import TurnContext
from .workspace_guard import WorkspaceViolation

PROJECT_REPAIR_PLAN_SCHEMA = "tiangong.l6_25.project_repair_plan.v1"
SENSITIVE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer|token|secret|password|credential)\s*[:=]\s*[^\s,;]+"
)
SENSITIVE_WORDS = ("api_key", "apikey", "authorization", "bearer", "token", "secret", "password", "credential")
PROTECTED_KERNEL_PREFIX = "tiangong_kernel/"


@dataclass(frozen=True)
class ProjectRadarSnapshot:
    """L6.25 给修复链消费的安全项目雷达摘要。"""

    root: str
    files_count: int
    dirs_count: int
    key_files: list[str] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)
    test_files: list[str] = field(default_factory=list)
    package_dirs: list[str] = field(default_factory=list)
    config_files: list[str] = field(default_factory=list)
    hot_paths: list[str] = field(default_factory=list)
    test_entry_hints: list[dict[str, Any]] = field(default_factory=list)
    risk_notes: list[str] = field(default_factory=list)
    truncated: bool = False

    def public_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "files_count": self.files_count,
            "dirs_count": self.dirs_count,
            "key_files": list(self.key_files),
            "entry_points": list(self.entry_points),
            "test_files": list(self.test_files),
            "package_dirs": list(self.package_dirs),
            "config_files": list(self.config_files),
            "hot_paths": list(self.hot_paths),
            "test_entry_hints": list(self.test_entry_hints),
            "risk_notes": list(self.risk_notes),
            "truncated": self.truncated,
        }


@dataclass(frozen=True)
class PatchPlanStep:
    step_id: str
    phase: str
    target_path: str
    operation: str
    risk_level: str
    rationale: str
    guardrails: list[str] = field(default_factory=list)
    expected_validation: list[str] = field(default_factory=list)
    applies_now: bool = False

    def __post_init__(self) -> None:
        if self.applies_now:
            raise ValueError("L6.25 PatchPlanStep must not apply patch immediately")

    def public_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "phase": self.phase,
            "target_path": self.target_path,
            "operation": self.operation,
            "risk_level": self.risk_level,
            "rationale": self.rationale,
            "guardrails": list(self.guardrails),
            "expected_validation": list(self.expected_validation),
            "applies_now": self.applies_now,
        }


@dataclass(frozen=True)
class RegressionHint:
    name: str
    command: str
    target: str
    priority: str
    reason: str
    allowlisted: bool = True

    def public_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "command": self.command,
            "target": self.target,
            "priority": self.priority,
            "reason": self.reason,
            "allowlisted": self.allowlisted,
        }


@dataclass(frozen=True)
class RollbackEvidence:
    strategy: str
    protected_paths: list[str] = field(default_factory=list)
    backup_required: bool = True
    hash_before_required: bool = True
    kernel_pollution_guard: bool = True
    rollback_notes: list[str] = field(default_factory=list)

    def public_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "protected_paths": list(self.protected_paths),
            "backup_required": self.backup_required,
            "hash_before_required": self.hash_before_required,
            "kernel_pollution_guard": self.kernel_pollution_guard,
            "rollback_notes": list(self.rollback_notes),
        }


@dataclass(frozen=True)
class ProjectRepairPlanReport:
    schema: str
    generated_at: float
    status: str
    summary: str
    project_radar: ProjectRadarSnapshot
    patch_plan: list[PatchPlanStep] = field(default_factory=list)
    regression_hints: list[RegressionHint] = field(default_factory=list)
    rollback_evidence: RollbackEvidence = field(default_factory=lambda: RollbackEvidence(strategy="write_adapter_backup_and_hash_compare"))
    diagnosis_status: str = "unknown"
    issue_count: int = 0
    quality_status: str = "unknown"
    available_runtime_tools: list[str] = field(default_factory=list)
    notes_used: bool = False
    execution_first: bool = True
    shell_only: bool = True
    kernel_pollution_guard: bool = True
    applies_patch: bool = False
    writes_file: bool = False
    modifies_kernel: bool = False
    modifies_core_runtime: bool = False
    registers_formal_tool: bool = False
    releases_tool_handle: bool = False
    activates_skill: bool = False
    bypasses_governance: bool = False

    def __post_init__(self) -> None:
        if not (self.execution_first and self.shell_only and self.kernel_pollution_guard):
            raise ValueError("L6.25 repair plan must remain execution-first, shell-only and kernel-guarded")
        forbidden = (
            self.applies_patch,
            self.writes_file,
            self.modifies_kernel,
            self.modifies_core_runtime,
            self.registers_formal_tool,
            self.releases_tool_handle,
            self.activates_skill,
            self.bypasses_governance,
        )
        if any(forbidden):
            raise ValueError("L6.25 repair plan cannot apply/write/mutate/register/release/activate/bypass governance")
        if any(step.applies_now for step in self.patch_plan):
            raise ValueError("L6.25 repair plan cannot contain immediate patch application")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "status": self.status,
            "summary": self.summary,
            "diagnosis_status": self.diagnosis_status,
            "issue_count": self.issue_count,
            "quality_status": self.quality_status,
            "project_radar": self.project_radar.public_dict(),
            "patch_plan": [step.public_dict() for step in self.patch_plan],
            "regression_hints": [hint.public_dict() for hint in self.regression_hints],
            "rollback_evidence": self.rollback_evidence.public_dict(),
            "available_runtime_tools": list(self.available_runtime_tools),
            "notes_used": self.notes_used,
            "execution_first": self.execution_first,
            "shell_only": self.shell_only,
            "kernel_pollution_guard": self.kernel_pollution_guard,
            "applies_patch": self.applies_patch,
            "writes_file": self.writes_file,
            "modifies_kernel": self.modifies_kernel,
            "modifies_core_runtime": self.modifies_core_runtime,
            "registers_formal_tool": self.registers_formal_tool,
            "releases_tool_handle": self.releases_tool_handle,
            "activates_skill": self.activates_skill,
            "bypasses_governance": self.bypasses_governance,
        }

    def summary_text(self) -> str:
        return (
            "L6.25 项目雷达 + 工程修复外壳闭环："
            f"status={self.status}；patch_steps={len(self.patch_plan)}；"
            f"regression_hints={len(self.regression_hints)}；diagnosis={self.diagnosis_status}；"
            f"quality={self.quality_status}；shell_only={self.shell_only}；kernel_pollution_guard={self.kernel_pollution_guard}。{self.summary}"
        )

    def markdown_report(self) -> str:
        lines = [
            "# 临渊者 L6.25 项目雷达与工程修复外壳闭环报告",
            "",
            f"- schema: `{self.schema}`",
            f"- status: `{self.status}`",
            f"- diagnosis_status: `{self.diagnosis_status}`",
            f"- quality_status: `{self.quality_status}`",
            f"- patch_steps: `{len(self.patch_plan)}`",
            f"- regression_hints: `{len(self.regression_hints)}`",
            f"- shell_only: `{self.shell_only}`",
            f"- kernel_pollution_guard: `{self.kernel_pollution_guard}`",
            "",
            "## 摘要",
            "",
            self.summary,
            "",
            "## 项目雷达",
            "",
            f"- files: `{self.project_radar.files_count}`",
            f"- dirs: `{self.project_radar.dirs_count}`",
            f"- entry_points: `{', '.join(self.project_radar.entry_points[:12]) or '<无>'}`",
            f"- test_files: `{', '.join(self.project_radar.test_files[:12]) or '<无>'}`",
            f"- hot_paths: `{', '.join(self.project_radar.hot_paths[:12]) or '<无>'}`",
            "",
            "## PatchPlan",
            "",
        ]
        if not self.patch_plan:
            lines.append("暂无补丁计划。")
        for step in self.patch_plan:
            lines.append(
                f"- `{step.step_id}` phase=`{step.phase}` target=`{step.target_path}` risk=`{step.risk_level}` operation={step.operation}"
            )
            lines.append(f"  - rationale: {step.rationale}")
        lines.extend(["", "## RegressionHint", ""])
        for hint in self.regression_hints:
            lines.append(f"- `{hint.name}` command=`{hint.command}` target=`{hint.target}` priority=`{hint.priority}`：{hint.reason}")
        lines.extend(["", "## RollbackEvidence", ""])
        lines.append(f"- strategy: `{self.rollback_evidence.strategy}`")
        lines.append(f"- protected_paths: `{', '.join(self.rollback_evidence.protected_paths)}`")
        lines.append(f"- backup_required: `{self.rollback_evidence.backup_required}`")
        lines.append(f"- hash_before_required: `{self.rollback_evidence.hash_before_required}`")
        lines.append("")
        lines.append("> L6.25 只生成工程修复外壳计划，不应用补丁、不写文件、不改 tiangong_kernel。")
        return "\n".join(lines)


class ProjectRepairPlanBridge:
    """项目雷达 + 工程修复计划桥。"""

    def __init__(self) -> None:
        self._last_report: ProjectRepairPlanReport | None = None

    @property
    def last_report(self) -> ProjectRepairPlanReport | None:
        return self._last_report

    def reset(self) -> None:
        self._last_report = None

    def build(
        self,
        *,
        snapshot: ProjectIndexSnapshot,
        diagnosis: dict[str, Any] | None = None,
        quality_results: list[dict[str, Any]] | None = None,
        available_tools: Iterable[str] = (),
        notes: str = "",
        max_targets: int = 12,
    ) -> ProjectRepairPlanReport:
        safe_notes = _safe_text(notes, limit=360)
        max_targets = max(1, min(int(max_targets or 12), 40))
        diagnosis = diagnosis if isinstance(diagnosis, dict) else {}
        quality_results = quality_results if isinstance(quality_results, list) else []
        tools = sorted({str(item) for item in available_tools})
        radar = _build_project_radar(snapshot, max_targets=max_targets)
        issues = diagnosis.get("issues", []) if isinstance(diagnosis.get("issues", []), list) else []
        patch_plan = _build_patch_plan(radar, issues, tools, max_targets=max_targets)
        regression_hints = _build_regression_hints(radar, quality_results)
        rollback = _build_rollback_evidence(patch_plan)
        diagnosis_status = str(diagnosis.get("status") or "empty")
        quality_status = _quality_status(quality_results)
        status = "repair_plan_ready"
        if any(item.get("status") == "failed" for item in quality_results if isinstance(item, dict)):
            status = "repair_plan_needs_fix"
        elif diagnosis_status in {"needs_repair", "has_warnings"}:
            status = "repair_plan_has_actions"
        summary = (
            "已把 L6.16 项目雷达、L6.17 工程诊断和受控质量检查摘要压缩为 PatchPlan / RegressionHint / "
            "RollbackEvidence；该报告只给 LLM 后续执行提供最小变更路线，不立即写入或套补丁。"
        )
        if safe_notes:
            summary += f" 用户备注：{safe_notes}"
        report = ProjectRepairPlanReport(
            schema=PROJECT_REPAIR_PLAN_SCHEMA,
            generated_at=time(),
            status=status,
            summary=summary,
            project_radar=radar,
            patch_plan=patch_plan,
            regression_hints=regression_hints,
            rollback_evidence=rollback,
            diagnosis_status=diagnosis_status,
            issue_count=len(issues),
            quality_status=quality_status,
            available_runtime_tools=tools,
            notes_used=bool(safe_notes),
        )
        self._last_report = report
        return report

    def public_dict(self) -> dict[str, Any]:
        if self._last_report is None:
            return {
                "schema": PROJECT_REPAIR_PLAN_SCHEMA,
                "status": "empty",
                "message": "暂无 L6.25 项目修复计划，请先执行 /repair-plan-build。",
            }
        return self._last_report.public_dict()

    def export_json(self, path: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def build_planner_hint(self) -> str:
        if self._last_report is None:
            return ""
        targets = ", ".join(step.target_path for step in self._last_report.patch_plan[:6])
        regressions = ", ".join(f"{hint.command}:{hint.target}" for hint in self._last_report.regression_hints[:4])
        return (
            "最近 L6.25 工程修复计划："
            f"status={self._last_report.status}; patch_steps={len(self._last_report.patch_plan)}; "
            f"targets={targets or '<none>'}; regression={regressions or '<none>'}; "
            "shell_only=True; apply_patch=False; kernel_pollution_guard=True"
        )[:1400]


def build_project_repair_plan_adapter(project_repair: ProjectRepairPlanBridge, project_index: Any, diagnostics: Any, state_provider: Any):
    def project_repair_plan_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        path = str(invocation.arguments.get("path") or ".")
        max_depth = int(invocation.arguments.get("max_depth") or 6)
        max_files = int(invocation.arguments.get("max_files") or 1500)
        try:
            snapshot = project_index.snapshot or project_index.scan(context.workspace, path=path, max_depth=max_depth, max_files=max_files)
            diagnosis = diagnostics.public_dict()
            if diagnosis.get("status") == "empty":
                diagnosis = diagnostics.diagnose(snapshot).public_dict()
            state = state_provider()
            report = project_repair.build(
                snapshot=snapshot,
                diagnosis=diagnosis,
                quality_results=_normalize_quality_results(invocation.arguments.get("quality_results") or []),
                available_tools=state.get("available_tools", []),
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
                max_targets=int(invocation.arguments.get("max_targets") or invocation.arguments.get("max_items") or 12),
            )
        except WorkspaceViolation as exc:
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.BLOCKED, str(exc), error_code="workspace_violation")
        except (TypeError, ValueError, OSError) as exc:
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.FAILED,
                f"L6.25 项目修复计划生成失败：{exc}",
                error_code="project_repair_plan_failed",
            )
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=report.summary_text(),
            data=report.public_dict(),
        )

    return project_repair_plan_adapter


def _build_project_radar(snapshot: ProjectIndexSnapshot, *, max_targets: int) -> ProjectRadarSnapshot:
    hot_paths = _dedupe(
        list(snapshot.entry_points[:8])
        + [path for path in _snapshot_sample_files_as_paths(snapshot) if _is_runtime_or_shell_path(path)]
        + list(snapshot.test_files[:8])
        + list(snapshot.key_files[:8])
    )[:max_targets]
    test_entry_hints = [
        {"name": "compileall", "command": "compileall", "target": snapshot.root or ".", "reason": "Python 语法层最小回归。"}
    ]
    if snapshot.test_files:
        test_entry_hints.append({"name": "pytest", "command": "pytest", "target": snapshot.root or ".", "reason": "发现 tests/test_*.py，建议作为第二层回归。"})
    else:
        test_entry_hints.append({"name": "pytest_after_smoke", "command": "pytest", "target": "tests", "reason": "当前缺少测试时，先补 smoke 后再运行。"})
    return ProjectRadarSnapshot(
        root=snapshot.root,
        files_count=snapshot.files_count,
        dirs_count=snapshot.dirs_count,
        key_files=list(snapshot.key_files[:80]),
        entry_points=list(snapshot.entry_points[:80]),
        test_files=list(snapshot.test_files[:120]),
        package_dirs=list(snapshot.package_dirs[:120]),
        config_files=list(snapshot.config_files[:120]),
        hot_paths=hot_paths,
        test_entry_hints=test_entry_hints,
        risk_notes=list(snapshot.risk_notes[:40]),
        truncated=snapshot.truncated,
    )


def _build_patch_plan(radar: ProjectRadarSnapshot, issues: list[Any], available_tools: list[str], *, max_targets: int) -> list[PatchPlanStep]:
    issue_codes = {str(item.get("code") or "") for item in issues if isinstance(item, dict)}
    steps: list[PatchPlanStep] = []
    if "read_file" in available_tools:
        for target in radar.hot_paths[: min(4, max_targets)]:
            steps.append(
                PatchPlanStep(
                    step_id=f"inspect_{len(steps)+1:02d}",
                    phase="inspect",
                    target_path=target,
                    operation="read_before_patch",
                    risk_level="A1",
                    rationale="先读取最小相关文件，避免盲改工程。",
                    guardrails=["只读", "不读取敏感路径", "不跨出工作区"],
                    expected_validation=["形成具体补丁点后再写入"],
                )
            )
    if "missing_readme" in issue_codes:
        steps.append(
            PatchPlanStep(
                step_id=f"patch_{len(steps)+1:02d}",
                phase="patch",
                target_path="README.md",
                operation="create_or_update_project_readme",
                risk_level="A3",
                rationale="诊断显示缺少 README，补充启动、测试与交付说明可提升长链执行续接。",
                guardrails=["经 write_workspace_file 写入", "覆盖前自动 .bak", "不写密钥/API 地址"],
                expected_validation=["compileall .", "检查 README 不含敏感凭据"],
            )
        )
    if "missing_tests" in issue_codes:
        steps.append(
            PatchPlanStep(
                step_id=f"patch_{len(steps)+1:02d}",
                phase="patch",
                target_path="tests/test_smoke.py",
                operation="add_minimal_smoke_test",
                risk_level="A3",
                rationale="诊断显示缺少测试锚点，先补最小 smoke，避免后续修复无复测闭环。",
                guardrails=["只补最小测试", "不依赖外部网络", "不触碰 tiangong_kernel"],
                expected_validation=["compileall .", "pytest tests -q"],
            )
        )
    if "missing_dependency_manifest" in issue_codes:
        steps.append(
            PatchPlanStep(
                step_id=f"patch_{len(steps)+1:02d}",
                phase="patch",
                target_path="pyproject.toml 或 requirements.txt",
                operation="add_reproducibility_manifest_if_absent",
                risk_level="A3",
                rationale="诊断显示缺少依赖/项目配置入口，需要补充可复现运行说明。",
                guardrails=["先优先补文档说明", "不要凭空锁定未知依赖版本", "正式依赖变更必须经质量门"],
                expected_validation=["compileall .", "pytest . -q（如存在 tests/）"],
            )
        )
    if "quality_check_failed" in issue_codes or any(_is_quality_check_failed_issue(item) for item in issues):
        target = radar.hot_paths[0] if radar.hot_paths else "."
        steps.append(
            PatchPlanStep(
                step_id=f"patch_{len(steps)+1:02d}",
                phase="patch",
                target_path=target,
                operation="minimal_failure_driven_patch",
                risk_level="A3",
                rationale="质量检查失败时，只允许基于失败摘要定位最小补丁点，禁止大面积重构。",
                guardrails=["先保留失败日志", "单次只改最小文件集", "改后立即运行同一质量检查"],
                expected_validation=["复跑失败的质量检查", "再跑 compileall ."],
            )
        )
    if not steps:
        steps.append(
            PatchPlanStep(
                step_id="no_patch_01",
                phase="noop",
                target_path=".",
                operation="no_patch_needed_keep_regression_loop",
                risk_level="A1",
                rationale="当前诊断未发现阻断项，保持只读项目雷达和回归提示即可。",
                guardrails=["不写文件", "不注册工具", "不改 tiangong_kernel"],
                expected_validation=["compileall .", "pytest . -q（如存在 tests/）"],
            )
        )
    return steps[:max_targets]


def _build_regression_hints(radar: ProjectRadarSnapshot, quality_results: list[dict[str, Any]]) -> list[RegressionHint]:
    hints = [
        RegressionHint("compileall_minimum", "compileall", radar.root or ".", "P0", "所有 Python 工程修复后的第一层语法回归。")
    ]
    if radar.test_files:
        hints.append(RegressionHint("pytest_detected_tests", "pytest", radar.root or ".", "P0", "已发现测试文件，修复后必须复跑 pytest。"))
    else:
        hints.append(RegressionHint("pytest_after_smoke_added", "pytest", "tests", "P1", "当前缺测试时，补 smoke 后以 tests/ 为复测锚点。"))
    failed = [item for item in quality_results if isinstance(item, dict) and item.get("status") == "failed"]
    for item in failed[:4]:
        command = "pytest" if "pytest" in str(item.get("argv") or item.get("command") or "") else "compileall"
        hints.append(
            RegressionHint(
                f"rerun_failed_{len(hints)+1}",
                command,
                radar.root or ".",
                "P0",
                "质量检查曾失败，修复后必须优先复跑同类检查。",
            )
        )
    hints.append(
        RegressionHint(
            "kernel_hash_compare",
            "manual_hash_compare",
            "tiangong_kernel",
            "P0",
            "壳装阶段必须证明 tiangong_kernel 没有新增、删除或变更。",
            allowlisted=False,
        )
    )
    return hints


def _build_rollback_evidence(patch_plan: list[PatchPlanStep]) -> RollbackEvidence:
    protected = sorted(_dedupe([PROTECTED_KERNEL_PREFIX] + [step.target_path for step in patch_plan if step.target_path.startswith(PROTECTED_KERNEL_PREFIX)]))
    notes = [
        "正式写入只能通过 write_workspace_file，由适配器自动生成 .bak 备份。",
        "正式发布前必须保存修改前后 hash，尤其 tiangong_kernel 必须 0 added / 0 changed / 0 deleted。",
        "PatchPlan 只是计划，不是补丁应用；失败时回滚到 .bak 或丢弃草案。",
    ]
    return RollbackEvidence(
        strategy="workspace_write_adapter_backup_plus_hash_compare",
        protected_paths=protected,
        backup_required=True,
        hash_before_required=True,
        kernel_pollution_guard=True,
        rollback_notes=notes,
    )


def _normalize_quality_results(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            out.append({str(key): item[key] for key in item if key in {"tool_name", "status", "error_code", "summary", "returncode", "argv", "audit_ref", "command"}})
    return out


def _quality_status(quality_results: list[dict[str, Any]]) -> str:
    if not quality_results:
        return "empty"
    if any(item.get("status") == "failed" for item in quality_results):
        return "failed"
    if any(item.get("status") == "blocked" for item in quality_results):
        return "blocked"
    if all(item.get("status") == "ok" for item in quality_results):
        return "ok"
    return "mixed"


def _is_quality_check_failed_issue(item: Any) -> bool:
    return isinstance(item, dict) and str(item.get("code") or "") == "quality_check_failed"


def _is_runtime_or_shell_path(path: str) -> bool:
    return path.startswith("tiangong_agent_runtime/") or path.startswith("tiangong_agent_shell/")


def _safe_text(value: Any, *, limit: int = 700) -> str:
    text = redact_text(str(value or ""))
    text = SENSITIVE_PATTERN.sub(lambda m: f"{m.group(1)}=<redacted>", text)
    for word in SENSITIVE_WORDS:
        text = re.sub(re.escape(word), f"{word[:2]}***", text, flags=re.IGNORECASE)
    return text.strip()[:limit]


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def stable_repair_plan_digest(report: ProjectRepairPlanReport) -> str:
    material = json.dumps(report.public_dict(), ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _snapshot_sample_files_as_paths(snapshot: ProjectIndexSnapshot) -> list[str]:
    files = getattr(snapshot, "sample_files", [])
    result: list[str] = []
    for item in files:
        if isinstance(item, dict):
            path = str(item.get("path") or "")
            if path:
                result.append(path)
    return result

