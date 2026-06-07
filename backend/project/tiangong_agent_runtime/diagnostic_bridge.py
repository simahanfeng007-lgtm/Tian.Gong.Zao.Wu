"""L6.17 工程诊断桥。

该桥属于外壳运行层：读取 L6.16 项目雷达的安全摘要与受控质量检查结果，
生成可公开的诊断问题、修复建议和下一步计划建议。它不直接修改源码，
不写长期记忆，不触碰 tiangong_kernel 主体。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import Any

from .project_index_bridge import ProjectIndexSnapshot
from .tool_result import ToolResult


@dataclass(frozen=True)
class DiagnosticIssue:
    code: str
    severity: str
    message: str
    evidence: list[str] = field(default_factory=list)
    suggested_actions: list[str] = field(default_factory=list)

    def public_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "evidence": list(self.evidence),
            "suggested_actions": list(self.suggested_actions),
        }


@dataclass(frozen=True)
class ProjectDiagnosis:
    schema: str
    generated_at: float
    root: str
    status: str
    summary: str
    issues: list[DiagnosticIssue] = field(default_factory=list)
    recommended_plan: list[dict[str, Any]] = field(default_factory=list)
    quality_results: list[dict[str, Any]] = field(default_factory=list)

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "root": self.root,
            "status": self.status,
            "summary": self.summary,
            "issues": [issue.public_dict() for issue in self.issues],
            "recommended_plan": list(self.recommended_plan),
            "quality_results": list(self.quality_results),
        }

    def summary_text(self) -> str:
        lines = [
            "L6.17 工程诊断结果：",
            f"- root: {self.root}",
            f"- status: {self.status}",
            f"- issues: {len(self.issues)}",
            f"- summary: {self.summary}",
        ]
        for issue in self.issues[:8]:
            lines.append(f"  - [{issue.severity}] {issue.code}: {issue.message}")
        return "\n".join(lines)

    def markdown_report(self) -> str:
        lines = [
            "# 天工造物 L6.17 工程诊断报告",
            "",
            f"- schema: `{self.schema}`",
            f"- root: `{self.root}`",
            f"- status: `{self.status}`",
            f"- issue_count: `{len(self.issues)}`",
            "",
            "## 摘要",
            "",
            self.summary,
            "",
            "## 问题清单",
            "",
        ]
        if not self.issues:
            lines.append("未发现阻断性结构问题。")
        for issue in self.issues:
            lines.extend([
                f"### {issue.code} [{issue.severity}]",
                "",
                issue.message,
                "",
            ])
            if issue.evidence:
                lines.append("证据：")
                for item in issue.evidence:
                    lines.append(f"- {item}")
                lines.append("")
            if issue.suggested_actions:
                lines.append("建议动作：")
                for item in issue.suggested_actions:
                    lines.append(f"- {item}")
                lines.append("")
        lines.extend(["## 建议计划", ""])
        for step in self.recommended_plan:
            lines.append(f"- `{step.get('tool_name')}` {json.dumps(step.get('arguments', {}), ensure_ascii=False)}")
        lines.append("")
        lines.extend(["## 质量检查摘要", ""])
        if not self.quality_results:
            lines.append("暂无质量检查结果。")
        for item in self.quality_results:
            lines.append(f"- {item.get('tool_name')}: {item.get('status')} {item.get('error_code') or ''}")
        lines.append("")
        lines.append("> 本报告仅包含安全摘要，不包含 API Key、完整源码、完整 prompt 或敏感凭据。")
        return "\n".join(lines)


class EngineeringDiagnosticBridge:
    """把项目索引与质量检查结果归一化为工程诊断。"""

    def __init__(self) -> None:
        self._last_diagnosis: ProjectDiagnosis | None = None

    @property
    def last_diagnosis(self) -> ProjectDiagnosis | None:
        return self._last_diagnosis

    def reset(self) -> None:
        self._last_diagnosis = None

    def diagnose(
        self,
        snapshot: ProjectIndexSnapshot,
        *,
        quality_results: list[ToolResult] | None = None,
    ) -> ProjectDiagnosis:
        issues: list[DiagnosticIssue] = []
        quality_summary = _quality_summary(quality_results or [])

        key_lower = {item.lower() for item in snapshot.key_files}
        if not any(name.startswith("readme") for name in key_lower):
            issues.append(
                DiagnosticIssue(
                    code="missing_readme",
                    severity="P2",
                    message="项目根或扫描范围内未发现 README，LLM 装甲缺少基础说明入口。",
                    evidence=["key_files 未包含 README"],
                    suggested_actions=["生成或补充 README.md", "在后续计划中优先读取现有说明文件"],
                )
            )
        if not snapshot.test_files:
            issues.append(
                DiagnosticIssue(
                    code="missing_tests",
                    severity="P1",
                    message="未发现测试文件，自动修复闭环缺少复测锚点。",
                    evidence=["test_files 为空"],
                    suggested_actions=["补充最小 smoke tests", "至少保留 compileall 作为第一层质量门"],
                )
            )
        if not any(name in key_lower for name in {"pyproject.toml", "requirements.txt", "setup.py", "package.json"}):
            issues.append(
                DiagnosticIssue(
                    code="missing_dependency_manifest",
                    severity="P2",
                    message="未发现常见依赖/项目配置入口，环境复现能力较弱。",
                    evidence=["缺少 pyproject/requirements/setup/package.json"],
                    suggested_actions=["补充依赖说明或项目配置", "在报告中标注运行环境假设"],
                )
            )
        if snapshot.risk_notes:
            issues.append(
                DiagnosticIssue(
                    code="sensitive_paths_skipped",
                    severity="P2",
                    message="扫描时发现并跳过敏感路径，后续报告/打包必须继续脱敏。",
                    evidence=snapshot.risk_notes[:8],
                    suggested_actions=["打包前执行 forbidden/secret scan", "不要把敏感路径写入公共投影"],
                )
            )
        for item in quality_summary:
            if item.get("status") == "failed":
                issues.append(
                    DiagnosticIssue(
                        code="quality_check_failed",
                        severity="P1",
                        message="受控质量检查失败，需要进入修复/复测循环。",
                        evidence=[str(item.get("summary", ""))[:500]],
                        suggested_actions=["读取失败摘要涉及文件", "生成最小补丁", "重新运行质量检查"],
                    )
                )
            elif item.get("status") == "blocked":
                issues.append(
                    DiagnosticIssue(
                        code="quality_check_blocked",
                        severity="P1",
                        message="质量检查被治理链阻断，需要先修正命令或工作区边界。",
                        evidence=[str(item.get("summary", ""))[:500]],
                        suggested_actions=["检查 target 是否越界", "仅使用 compileall/pytest allowlist"],
                    )
                )

        status = "ok" if not issues else ("needs_repair" if any(issue.severity in {"P0", "P1"} for issue in issues) else "has_warnings")
        recommended_plan = _build_recommended_plan(snapshot, issues)
        diagnosis = ProjectDiagnosis(
            schema="tiangong.l6_17.engineering_diagnosis.v1",
            generated_at=time(),
            root=snapshot.root,
            status=status,
            summary=_build_summary(status, issues, snapshot, quality_summary),
            issues=issues,
            recommended_plan=recommended_plan,
            quality_results=quality_summary,
        )
        self._last_diagnosis = diagnosis
        return diagnosis

    def public_dict(self) -> dict[str, Any]:
        if self._last_diagnosis is None:
            return {"schema": "tiangong.l6_17.engineering_diagnosis.v1", "status": "empty", "message": "暂无工程诊断，请先执行 /diagnose。"}
        return self._last_diagnosis.public_dict()

    def export_json(self, path: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return target


def _quality_summary(results: list[ToolResult]) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for result in results:
        if result.tool_name != "run_python_quality_check":
            continue
        payload.append(
            {
                "tool_name": result.tool_name,
                "status": result.status.value,
                "error_code": result.error_code,
                "summary": result.output_summary[:1200],
                "returncode": result.data.get("returncode"),
            }
        )
    return payload


def _build_recommended_plan(snapshot: ProjectIndexSnapshot, issues: list[DiagnosticIssue]) -> list[dict[str, Any]]:
    plan: list[dict[str, Any]] = [
        {"tool_name": "scan_project", "arguments": {"path": snapshot.root or "."}},
        {"tool_name": "run_python_quality_check", "arguments": {"command": "compileall", "target": "."}},
    ]
    if snapshot.test_files:
        plan.append({"tool_name": "run_python_quality_check", "arguments": {"command": "pytest", "target": "."}})
    if any(issue.code == "missing_readme" for issue in issues):
        plan.append(
            {
                "tool_name": "write_workspace_file",
                "arguments": {"path": "README.md", "content": "# Project\n\nTODO: 补充项目说明、启动方式与测试方式。\n"},
            }
        )
    plan.append({"tool_name": "write_workspace_file", "arguments": {"path": "reports/l6_17_diagnosis.md", "content": "<由 Runtime 生成>"}})
    return plan


def _build_summary(status: str, issues: list[DiagnosticIssue], snapshot: ProjectIndexSnapshot, quality_summary: list[dict[str, Any]]) -> str:
    if not issues:
        return f"项目结构基础信号正常：files={snapshot.files_count}, tests={len(snapshot.test_files)}, quality_checks={len(quality_summary)}。"
    p1 = sum(1 for issue in issues if issue.severity in {"P0", "P1"})
    p2 = sum(1 for issue in issues if issue.severity == "P2")
    return f"诊断状态={status}；发现 {len(issues)} 个问题，其中 P0/P1={p1}，P2={p2}。"
