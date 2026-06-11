"""L6.18 测试验证质量门桥。

该桥把项目扫描、Python 质量检查和工程诊断的安全摘要归一为质量门裁决。
它不执行测试、不修改文件、不读取完整源码；真实执行仍由 Runtime 工具链完成。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import Any

from .tool_result import ToolResult


@dataclass(frozen=True)
class QualityGateIssue:
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
class QualityGateVerdict:
    schema: str
    generated_at: float
    gate_name: str
    decision: str
    allow_package: bool
    allow_continue: bool
    summary: str
    severity_counts: dict[str, int] = field(default_factory=dict)
    checks: list[dict[str, Any]] = field(default_factory=list)
    issues: list[QualityGateIssue] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "gate_name": self.gate_name,
            "decision": self.decision,
            "allow_package": self.allow_package,
            "allow_continue": self.allow_continue,
            "summary": self.summary,
            "severity_counts": dict(self.severity_counts),
            "checks": list(self.checks),
            "issues": [issue.public_dict() for issue in self.issues],
            "recommended_actions": list(self.recommended_actions),
        }

    def summary_text(self) -> str:
        lines = [
            "L6.18 质量门裁决：",
            f"- gate: {self.gate_name}",
            f"- decision: {self.decision}",
            f"- allow_package: {self.allow_package}",
            f"- allow_continue: {self.allow_continue}",
            f"- issues: {len(self.issues)}",
            f"- summary: {self.summary}",
        ]
        for issue in self.issues[:8]:
            lines.append(f"  - [{issue.severity}] {issue.code}: {issue.message}")
        return "\n".join(lines)

    def markdown_report(self) -> str:
        lines = [
            "# 临渊者 L6.18 测试验证质量门报告",
            "",
            f"- schema: `{self.schema}`",
            f"- gate: `{self.gate_name}`",
            f"- decision: `{self.decision}`",
            f"- allow_package: `{self.allow_package}`",
            f"- allow_continue: `{self.allow_continue}`",
            "",
            "## 摘要",
            "",
            self.summary,
            "",
            "## 检查项",
            "",
        ]
        if not self.checks:
            lines.append("暂无检查项。")
        for check in self.checks:
            lines.append(
                f"- `{check.get('name')}` status=`{check.get('status')}` code=`{check.get('error_code') or ''}`"
            )
        lines.extend(["", "## 问题", ""])
        if not self.issues:
            lines.append("未发现阻断性问题。")
        for issue in self.issues:
            lines.extend([f"### {issue.code} [{issue.severity}]", "", issue.message, ""])
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
        lines.extend(["## 推荐动作", ""])
        if not self.recommended_actions:
            lines.append("无额外推荐动作。")
        for action in self.recommended_actions:
            lines.append(f"- {action}")
        lines.append("")
        lines.append("> 本报告仅包含安全摘要，不包含 API Key、完整 prompt、完整源码或敏感凭据。")
        return "\n".join(lines)


class QualityGateBridge:
    """L6.18 质量门状态与裁决器。"""

    def __init__(self) -> None:
        self._last_verdict: QualityGateVerdict | None = None

    @property
    def last_verdict(self) -> QualityGateVerdict | None:
        return self._last_verdict

    def reset(self) -> None:
        self._last_verdict = None

    def evaluate(
        self,
        *,
        gate_name: str = "default",
        quality_results: list[ToolResult | dict[str, Any]] | None = None,
        diagnosis: dict[str, Any] | None = None,
        require_pytest: bool = False,
    ) -> QualityGateVerdict:
        checks = _normalize_quality_results(quality_results or [])
        issues: list[QualityGateIssue] = []
        recommended_actions: list[str] = []

        if not checks:
            issues.append(
                QualityGateIssue(
                    code="no_quality_checks",
                    severity="P2",
                    message="未发现质量检查结果，不能把当前状态视为完整验收。",
                    evidence=["quality_results 为空"],
                    suggested_actions=["至少执行 compileall", "如存在 tests/，执行 pytest"],
                )
            )

        has_compileall = any(check.get("command") == "compileall" or "compileall" in str(check.get("argv", "")) for check in checks)
        has_pytest = any(check.get("command") == "pytest" or "pytest" in str(check.get("argv", "")) for check in checks)
        if not has_compileall:
            issues.append(
                QualityGateIssue(
                    code="compileall_missing",
                    severity="P1",
                    message="缺少 compileall 质量检查，Python 语法层未验收。",
                    evidence=["未发现 compileall 检查项"],
                    suggested_actions=["运行 run_python_quality_check(command=compileall)"],
                )
            )
        if require_pytest and not has_pytest:
            issues.append(
                QualityGateIssue(
                    code="pytest_missing",
                    severity="P1",
                    message="当前质量门要求 pytest，但未发现 pytest 结果。",
                    evidence=["require_pytest=True 且未发现 pytest 检查项"],
                    suggested_actions=["运行 run_python_quality_check(command=pytest)", "没有测试时先补 smoke test 或降低 gate 策略"],
                )
            )

        for check in checks:
            status = str(check.get("status") or "").lower()
            name = str(check.get("name") or check.get("tool_name") or "quality_check")
            if status == "blocked":
                issues.append(
                    QualityGateIssue(
                        code="quality_check_blocked",
                        severity="P0",
                        message=f"质量检查 {name} 被 adapter 标记 blocked；L6.72.39 下仅作为非 A5 警告进入报告。",
                        evidence=[str(check.get("summary", ""))[:700]],
                        suggested_actions=["修正工作区边界或命令 allowlist", "禁止绕过 Runtime 直接执行"],
                    )
                )
            elif status == "failed":
                issues.append(
                    QualityGateIssue(
                        code="quality_check_failed",
                        severity="P1",
                        message=f"质量检查 {name} 失败；L6.72.39 下允许继续执行，但建议修复后复测。",
                        evidence=[str(check.get("summary", ""))[:900]],
                        suggested_actions=["读取失败摘要涉及文件", "生成最小修复补丁", "重新运行质量门"],
                    )
                )

        diagnosis = diagnosis or {}
        for item in diagnosis.get("issues", []) if isinstance(diagnosis, dict) else []:
            severity = str(item.get("severity") or "P3").upper()
            code = str(item.get("code") or "diagnosis_issue")
            if severity in {"P0", "P1"}:
                issues.append(
                    QualityGateIssue(
                        code=f"diagnosis_{code}",
                        severity=severity,
                        message=str(item.get("message") or "诊断发现阻断/高优问题。"),
                        evidence=[str(x) for x in item.get("evidence", [])][:8],
                        suggested_actions=[str(x) for x in item.get("suggested_actions", [])][:8],
                    )
                )
            elif severity == "P2":
                issues.append(
                    QualityGateIssue(
                        code=f"diagnosis_{code}",
                        severity="P2",
                        message=str(item.get("message") or "诊断发现警告。"),
                        evidence=[str(x) for x in item.get("evidence", [])][:8],
                        suggested_actions=[str(x) for x in item.get("suggested_actions", [])][:8],
                    )
                )

        severity_counts = _count_severity(issues)
        # L6.72.39：QualityGate 不删除，但只对 A5 级问题硬阻断。P0/P1/P2 质量问题
        # 转为继续执行/打包前提示，避免非 A5 门槛压制代码编辑执行力。
        has_a5_issue = any("A5" in (issue.code + " " + issue.message + " " + " ".join(issue.evidence)).upper() for issue in issues)
        if has_a5_issue:
            decision = "blocked"
            allow_package = False
            allow_continue = False
            summary = "质量门 A5 阻断：存在极高危、凭证或不可逆破坏风险。"
        elif severity_counts.get("P0", 0) > 0 or severity_counts.get("P1", 0) > 0:
            decision = "warn"
            allow_package = True
            allow_continue = True
            summary = "质量门非 A5 警告：允许继续执行和打包，但必须在报告中披露失败/警告项并建议复测。"
        elif severity_counts.get("P2", 0) > 0:
            decision = "warn"
            allow_package = True
            allow_continue = True
            summary = "质量门提示：存在 P2 警告，允许继续。"
        else:
            decision = "pass"
            allow_package = True
            allow_continue = True
            summary = "质量门通过：基础质量检查与诊断摘要未发现 A5 阻断项。"

        recommended_actions.extend(_recommend_actions(decision, issues))
        verdict = QualityGateVerdict(
            schema="tiangong.l6_18.quality_gate.v1",
            generated_at=time(),
            gate_name=gate_name,
            decision=decision,
            allow_package=allow_package,
            allow_continue=allow_continue,
            summary=summary,
            severity_counts=severity_counts,
            checks=checks,
            issues=issues,
            recommended_actions=recommended_actions,
        )
        self._last_verdict = verdict
        return verdict

    def public_dict(self) -> dict[str, Any]:
        if self._last_verdict is None:
            return {"schema": "tiangong.l6_18.quality_gate.v1", "status": "empty", "message": "暂无质量门裁决，请先执行 /quality-gate。"}
        return self._last_verdict.public_dict()

    def export_json(self, path: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return target


def _normalize_quality_results(results: list[ToolResult | dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for item in results:
        if isinstance(item, ToolResult):
            if item.tool_name != "run_python_quality_check":
                continue
            argv = item.data.get("argv") or []
            command = "pytest" if "pytest" in " ".join(str(x) for x in argv) else "compileall" if "compileall" in " ".join(str(x) for x in argv) else "quality_check"
            checks.append(
                {
                    "name": command,
                    "tool_name": item.tool_name,
                    "command": command,
                    "status": item.status.value,
                    "error_code": item.error_code,
                    "summary": item.output_summary[:1500],
                    "returncode": item.data.get("returncode"),
                    "argv": argv,
                    "audit_ref": item.audit_ref,
                }
            )
            continue
        if isinstance(item, dict):
            status = str(item.get("status") or "")
            if not status and "ok" in item:
                status = "ok" if item.get("ok") else "failed"
            argv = item.get("argv") or []
            argv_text = " ".join(str(x) for x in argv)
            inferred_command = item.get("command") or item.get("name")
            if not inferred_command:
                if "pytest" in argv_text:
                    inferred_command = "pytest"
                elif "compileall" in argv_text:
                    inferred_command = "compileall"
                else:
                    inferred_command = "quality_check"
            checks.append(
                {
                    "name": inferred_command,
                    "tool_name": item.get("tool_name") or "run_python_quality_check",
                    "command": inferred_command,
                    "status": status,
                    "error_code": item.get("error_code") or "",
                    "summary": str(item.get("summary") or item.get("output_summary") or "")[:1500],
                    "returncode": item.get("returncode"),
                    "argv": argv,
                    "audit_ref": item.get("audit_ref") or "",
                }
            )
    return checks


def _count_severity(issues: list[QualityGateIssue]) -> dict[str, int]:
    counts = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    for issue in issues:
        key = issue.severity.upper()
        counts[key] = counts.get(key, 0) + 1
    return counts


def _recommend_actions(decision: str, issues: list[QualityGateIssue]) -> list[str]:
    if decision == "pass":
        return ["允许进入交付打包或产品化下一阶段。"]
    if decision == "warn":
        return ["允许受控打包，但必须在交付报告中披露 P2 警告。", "优先修复可低成本消除的文档/依赖/测试覆盖问题。"]
    if decision == "fail":
        return ["禁止发布打包。", "进入诊断→修复→复测循环。", "质量门再次通过前不得宣称可交付。"]
    return ["停止自动链路。", "先修正治理阻断、越界路径或危险命令。"]
