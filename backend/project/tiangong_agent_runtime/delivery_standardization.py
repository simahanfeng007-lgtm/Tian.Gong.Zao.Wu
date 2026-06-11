"""L6.26 交付链标准化外壳。

该模块把 L6.16-L6.25 已有项目雷达、诊断、质量门、交付 Manifest、
工程修复计划和十八系统壳装状态压缩为统一的交付证据报告：
ChangeSet / TestEvidence / ManifestEvidence / IntegrityEvidence / TodoReport。

它只在 Runtime 外壳层生成可公开摘要，不构建正式发布 ZIP、不写源码、不应用补丁、
不注册工具、不激活 Skill、不释放正式工具句柄，也不修改 tiangong_kernel。
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
from .workspace_guard import WorkspaceViolation

DELIVERY_STANDARDIZATION_SCHEMA = "tiangong.l6_26.delivery_standardization.v1"
SENSITIVE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer|token|secret|password|credential)\s*[:=]\s*[^\s,;]+"
)
SENSITIVE_WORDS = ("api_key", "apikey", "authorization", "bearer", "token", "secret", "password", "credential")


@dataclass(frozen=True)
class ChangeRecord:
    """交付报告中的最小修改清单项。"""

    path: str
    action: str
    category: str
    summary: str
    evidence_refs: list[str] = field(default_factory=list)
    risk_level: str = "A2"
    kernel_path: bool = False

    def public_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "action": self.action,
            "category": self.category,
            "summary": self.summary,
            "evidence_refs": list(self.evidence_refs),
            "risk_level": self.risk_level,
            "kernel_path": self.kernel_path,
        }


@dataclass(frozen=True)
class TestEvidenceRecord:
    """标准化测试/质量证据。"""

    name: str
    status: str
    command: str = ""
    target: str = ""
    source: str = ""
    returncode: int | None = None
    summary: str = ""
    required_for_release: bool = True

    def public_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "command": self.command,
            "target": self.target,
            "source": self.source,
            "returncode": self.returncode,
            "summary": self.summary,
            "required_for_release": self.required_for_release,
        }


@dataclass(frozen=True)
class ManifestEvidence:
    """交付 Manifest 证据摘要。"""

    schema: str
    status: str
    release_gate_decision: str = ""
    allow_release: bool = False
    payload_files: int = 0
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    bundle_sha256: str = ""
    manifest_available: bool = False

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "status": self.status,
            "release_gate_decision": self.release_gate_decision,
            "allow_release": self.allow_release,
            "payload_files": self.payload_files,
            "artifacts": list(self.artifacts),
            "bundle_sha256": self.bundle_sha256,
            "manifest_available": self.manifest_available,
        }


@dataclass(frozen=True)
class IntegrityEvidence:
    """交付完整性证据。"""

    report_digest: str
    manifest_digest: str = ""
    bundle_sha256: str = ""
    artifact_count: int = 0
    sha256_sidecar_present: bool = False
    kernel_pollution_guard: bool = True
    protected_paths: list[str] = field(default_factory=lambda: ["tiangong_kernel/"])

    def public_dict(self) -> dict[str, Any]:
        return {
            "report_digest": self.report_digest,
            "manifest_digest": self.manifest_digest,
            "bundle_sha256": self.bundle_sha256,
            "artifact_count": self.artifact_count,
            "sha256_sidecar_present": self.sha256_sidecar_present,
            "kernel_pollution_guard": self.kernel_pollution_guard,
            "protected_paths": list(self.protected_paths),
        }


@dataclass(frozen=True)
class TodoItem:
    """未做事项/下一步交付缺口。"""

    item_id: str
    priority: str
    description: str
    reason: str
    owner_systems: list[str] = field(default_factory=list)

    def public_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "priority": self.priority,
            "description": self.description,
            "reason": self.reason,
            "owner_systems": list(self.owner_systems),
        }


@dataclass(frozen=True)
class DeliveryStandardizationReport:
    """L6.26 标准化交付证据报告。"""

    schema: str
    generated_at: float
    status: str
    summary: str
    baseline: str = "L6.25-project-repair-shell"
    change_set: list[ChangeRecord] = field(default_factory=list)
    test_evidence: list[TestEvidenceRecord] = field(default_factory=list)
    manifest_evidence: ManifestEvidence = field(
        default_factory=lambda: ManifestEvidence(
            schema="tiangong.l6_19.delivery_manifest.v1",
            status="empty",
            manifest_available=False,
        )
    )
    integrity_evidence: IntegrityEvidence = field(default_factory=lambda: IntegrityEvidence(report_digest=""))
    todo_report: list[TodoItem] = field(default_factory=list)
    audit_summary: list[dict[str, Any]] = field(default_factory=list)
    quality_decision: str = "unknown"
    release_ready: bool = False
    execution_first: bool = True
    shell_only: bool = True
    kernel_pollution_guard: bool = True
    creates_release_bundle: bool = False
    writes_file: bool = False
    applies_patch: bool = False
    modifies_kernel: bool = False
    modifies_core_runtime: bool = False
    registers_formal_tool: bool = False
    releases_tool_handle: bool = False
    activates_skill: bool = False
    bypasses_governance: bool = False

    def __post_init__(self) -> None:
        if not (self.execution_first and self.shell_only and self.kernel_pollution_guard):
            raise ValueError("L6.26 delivery standardization must remain execution-first, shell-only and kernel-guarded")
        forbidden = (
            self.creates_release_bundle,
            self.writes_file,
            self.applies_patch,
            self.modifies_kernel,
            self.modifies_core_runtime,
            self.registers_formal_tool,
            self.releases_tool_handle,
            self.activates_skill,
            self.bypasses_governance,
        )
        if any(forbidden):
            raise ValueError("L6.26 delivery standardization cannot bundle/write/patch/mutate/register/release/activate/bypass governance")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "status": self.status,
            "summary": self.summary,
            "baseline": self.baseline,
            "change_set": [item.public_dict() for item in self.change_set],
            "test_evidence": [item.public_dict() for item in self.test_evidence],
            "manifest_evidence": self.manifest_evidence.public_dict(),
            "integrity_evidence": self.integrity_evidence.public_dict(),
            "todo_report": [item.public_dict() for item in self.todo_report],
            "audit_summary": list(self.audit_summary),
            "quality_decision": self.quality_decision,
            "release_ready": self.release_ready,
            "execution_first": self.execution_first,
            "shell_only": self.shell_only,
            "kernel_pollution_guard": self.kernel_pollution_guard,
            "creates_release_bundle": self.creates_release_bundle,
            "writes_file": self.writes_file,
            "applies_patch": self.applies_patch,
            "modifies_kernel": self.modifies_kernel,
            "modifies_core_runtime": self.modifies_core_runtime,
            "registers_formal_tool": self.registers_formal_tool,
            "releases_tool_handle": self.releases_tool_handle,
            "activates_skill": self.activates_skill,
            "bypasses_governance": self.bypasses_governance,
        }

    def summary_text(self) -> str:
        return (
            "L6.26 标准化交付证据："
            f"status={self.status}；changes={len(self.change_set)}；"
            f"tests={len(self.test_evidence)}；todos={len(self.todo_report)}；"
            f"quality={self.quality_decision}；release_ready={self.release_ready}；"
            f"shell_only={self.shell_only}；kernel_pollution_guard={self.kernel_pollution_guard}。{self.summary}"
        )

    def markdown_report(self) -> str:
        lines = [
            "# 临渊者 L6.26 交付链标准化报告",
            "",
            f"- schema: `{self.schema}`",
            f"- status: `{self.status}`",
            f"- baseline: `{self.baseline}`",
            f"- quality_decision: `{self.quality_decision}`",
            f"- release_ready: `{self.release_ready}`",
            f"- shell_only: `{self.shell_only}`",
            f"- kernel_pollution_guard: `{self.kernel_pollution_guard}`",
            "",
            "## 摘要",
            "",
            self.summary,
            "",
            "## 修改清单 ChangeSet",
            "",
        ]
        if not self.change_set:
            lines.append("暂无标准化修改清单。")
        for item in self.change_set:
            lines.append(f"- `{item.path}` action=`{item.action}` category=`{item.category}` risk=`{item.risk_level}`：{item.summary}")
        lines.extend(["", "## 测试证据 TestEvidence", ""])
        if not self.test_evidence:
            lines.append("暂无测试证据。")
        for item in self.test_evidence:
            lines.append(f"- `{item.name}` status=`{item.status}` command=`{item.command}` target=`{item.target}` source=`{item.source}`")
        lines.extend(["", "## ManifestEvidence", ""])
        lines.append(f"- manifest_available: `{self.manifest_evidence.manifest_available}`")
        lines.append(f"- release_gate: `{self.manifest_evidence.release_gate_decision}`")
        lines.append(f"- allow_release: `{self.manifest_evidence.allow_release}`")
        lines.append(f"- bundle_sha256: `{self.manifest_evidence.bundle_sha256 or '<none>'}`")
        lines.extend(["", "## IntegrityEvidence", ""])
        lines.append(f"- report_digest: `{self.integrity_evidence.report_digest}`")
        lines.append(f"- manifest_digest: `{self.integrity_evidence.manifest_digest or '<none>'}`")
        lines.append(f"- sha256_sidecar_present: `{self.integrity_evidence.sha256_sidecar_present}`")
        lines.extend(["", "## 未做事项 TodoReport", ""])
        if not self.todo_report:
            lines.append("暂无未做事项。")
        for item in self.todo_report:
            lines.append(f"- `{item.item_id}` [{item.priority}] {item.description}：{item.reason}")
        lines.append("")
        lines.append("> 本报告只保存交付证据摘要，不包含 API Key、完整 prompt、完整源码、完整内部路径或敏感凭证。")
        return "\n".join(lines)


class DeliveryStandardizationBridge:
    """保存最近一次 L6.26 交付链标准化报告。"""

    def __init__(self) -> None:
        self._last_report: DeliveryStandardizationReport | None = None

    @property
    def last_report(self) -> DeliveryStandardizationReport | None:
        return self._last_report

    def reset(self) -> None:
        self._last_report = None

    def remember(self, report: DeliveryStandardizationReport) -> DeliveryStandardizationReport:
        self._last_report = report
        return report

    def build(
        self,
        *,
        quality_gate: dict[str, Any] | None = None,
        diagnosis: dict[str, Any] | None = None,
        delivery_manifest: dict[str, Any] | None = None,
        project_repair: dict[str, Any] | None = None,
        shell_mount: dict[str, Any] | None = None,
        audit_summary: list[dict[str, Any]] | None = None,
        notes: str = "",
    ) -> DeliveryStandardizationReport:
        quality_gate = quality_gate or {}
        diagnosis = diagnosis or {}
        delivery_manifest = delivery_manifest or {}
        project_repair = project_repair or {}
        shell_mount = shell_mount or {}
        audit_summary = audit_summary or []

        change_set = _build_change_set(project_repair, shell_mount)
        test_evidence = _build_test_evidence(quality_gate, diagnosis, project_repair)
        manifest_evidence = _build_manifest_evidence(delivery_manifest)
        todo_report = _build_todo_report(quality_gate, test_evidence, manifest_evidence, project_repair, shell_mount)
        quality_decision = str(quality_gate.get("decision") or quality_gate.get("status") or "unknown")
        release_ready = _release_ready(quality_gate, test_evidence, manifest_evidence)
        safe_notes = _redact(notes)[:900]
        summary = _build_summary(
            quality_decision=quality_decision,
            release_ready=release_ready,
            change_count=len(change_set),
            test_count=len(test_evidence),
            todo_count=len(todo_report),
            notes=safe_notes,
        )
        base_payload = {
            "schema": DELIVERY_STANDARDIZATION_SCHEMA,
            "summary": summary,
            "quality_decision": quality_decision,
            "release_ready": release_ready,
            "changes": [item.public_dict() for item in change_set],
            "tests": [item.public_dict() for item in test_evidence],
            "manifest": manifest_evidence.public_dict(),
            "todos": [item.public_dict() for item in todo_report],
        }
        report_digest = _stable_digest(base_payload)
        manifest_digest = _stable_digest(delivery_manifest) if delivery_manifest and delivery_manifest.get("status") != "empty" else ""
        artifact_count = len(manifest_evidence.artifacts)
        sha_sidecar = any(str(item.get("path") or "").endswith(".sha256") for item in manifest_evidence.artifacts)
        integrity = IntegrityEvidence(
            report_digest=report_digest,
            manifest_digest=manifest_digest,
            bundle_sha256=manifest_evidence.bundle_sha256,
            artifact_count=artifact_count,
            sha256_sidecar_present=sha_sidecar or bool(manifest_evidence.bundle_sha256),
            kernel_pollution_guard=True,
        )
        status = "delivery_standard_ready" if release_ready else "delivery_standard_has_open_items"
        if quality_decision in {"fail", "blocked"}:
            status = "delivery_standard_needs_fix"
        report = DeliveryStandardizationReport(
            schema=DELIVERY_STANDARDIZATION_SCHEMA,
            generated_at=time(),
            status=status,
            summary=summary,
            change_set=change_set,
            test_evidence=test_evidence,
            manifest_evidence=manifest_evidence,
            integrity_evidence=integrity,
            todo_report=todo_report,
            audit_summary=_sanitize_audit(audit_summary[-30:]),
            quality_decision=quality_decision,
            release_ready=release_ready,
        )
        self._last_report = report
        return report

    def public_dict(self) -> dict[str, Any]:
        if self._last_report is None:
            return {
                "schema": DELIVERY_STANDARDIZATION_SCHEMA,
                "status": "empty",
                "message": "暂无 L6.26 交付链标准化报告，请先执行 /delivery-standard-build。",
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
        payload = self._last_report.public_dict()
        digest = payload.get("integrity_evidence", {}).get("report_digest", "")
        return (
            "L6.26 交付链标准化已生成："
            f"status={payload.get('status')}；quality={payload.get('quality_decision')}；"
            f"release_ready={payload.get('release_ready')}；changes={len(payload.get('change_set', []))}；"
            f"tests={len(payload.get('test_evidence', []))}；todos={len(payload.get('todo_report', []))}；digest={digest[:12]}。"
        )


def build_delivery_standardization_adapter(
    bridge: DeliveryStandardizationBridge,
    quality_gate_bridge: Any,
    diagnostics: Any,
    delivery_bridge: Any,
    project_repair_bridge: Any,
    shell_mount_bridge: Any,
    audit_bridge: Any,
):
    def delivery_standardization_adapter(invocation: ToolInvocation, context: Any) -> ToolResult:
        try:
            report = bridge.build(
                quality_gate=quality_gate_bridge.public_dict(),
                diagnosis=diagnostics.public_dict(),
                delivery_manifest=delivery_bridge.public_dict(),
                project_repair=project_repair_bridge.public_dict(),
                shell_mount=shell_mount_bridge.public_dict(),
                audit_summary=audit_bridge.recent_summary(),
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
            )
            return ToolResult(
                step_id=invocation.step_id,
                tool_name=invocation.tool_name,
                status=ToolResultStatus.OK,
                output_summary=report.summary_text(),
                data=report.public_dict(),
            )
        except (ValueError, WorkspaceViolation) as exc:
            return ToolResult(
                step_id=invocation.step_id,
                tool_name=invocation.tool_name,
                status=ToolResultStatus.BLOCKED,
                output_summary=f"L6.26 交付链标准化被阻断：{exc}",
                error_code="delivery_standardization_blocked",
            )
        except OSError as exc:
            return ToolResult(
                step_id=invocation.step_id,
                tool_name=invocation.tool_name,
                status=ToolResultStatus.FAILED,
                output_summary=f"L6.26 交付链标准化失败：{exc}",
                error_code="delivery_standardization_failed",
            )

    return delivery_standardization_adapter


def stable_delivery_standard_digest(report: DeliveryStandardizationReport) -> str:
    payload = report.public_dict()
    payload.pop("generated_at", None)
    return _stable_digest(payload)


def _build_change_set(project_repair: dict[str, Any], shell_mount: dict[str, Any]) -> list[ChangeRecord]:
    records: list[ChangeRecord] = []
    seen: set[str] = set()
    for step in project_repair.get("patch_plan", []) if isinstance(project_repair, dict) else []:
        target = _clean_path(str(step.get("target_path") or ""))
        if not target or target in seen:
            continue
        seen.add(target)
        records.append(
            ChangeRecord(
                path=target,
                action="planned_change",
                category=str(step.get("phase") or "repair_plan"),
                summary=_redact(str(step.get("rationale") or step.get("operation") or "L6.25 PatchPlan 候选变更。"))[:500],
                evidence_refs=[str(step.get("step_id") or "patch_plan")],
                risk_level=str(step.get("risk_level") or "A2"),
                kernel_path=target.startswith("tiangong_kernel/"),
            )
        )
    if shell_mount.get("status") not in {None, "", "empty"}:
        records.append(
            ChangeRecord(
                path="tiangong_agent_runtime/shell_system_mount.py",
                action="existing_shell_mount",
                category="runtime_shell",
                summary="L6.24 十八系统壳装总线已提供系统槽位与 Planner 可读挂载图。",
                evidence_refs=["shell_mount"],
                risk_level="A2",
                kernel_path=False,
            )
        )
    if project_repair.get("status") not in {None, "", "empty"}:
        records.append(
            ChangeRecord(
                path="tiangong_agent_runtime/project_repair_plan.py",
                action="existing_repair_shell",
                category="runtime_shell",
                summary="L6.25 已提供 ProjectRadarSnapshot / PatchPlan / RegressionHint / RollbackEvidence。",
                evidence_refs=["project_repair"],
                risk_level="A2",
                kernel_path=False,
            )
        )
    if not records:
        records.append(
            ChangeRecord(
                path="<no-change-set>",
                action="needs_input",
                category="delivery_gap",
                summary="尚未发现可标准化的修改清单；建议先运行项目雷达、质量门或工程修复计划。",
                evidence_refs=[],
                risk_level="A1",
                kernel_path=False,
            )
        )
    return records[:50]


def _build_test_evidence(
    quality_gate: dict[str, Any], diagnosis: dict[str, Any], project_repair: dict[str, Any]
) -> list[TestEvidenceRecord]:
    records: list[TestEvidenceRecord] = []
    for check in quality_gate.get("checks", []) if isinstance(quality_gate, dict) else []:
        records.append(
            TestEvidenceRecord(
                name=str(check.get("name") or check.get("tool_name") or "quality_check"),
                status=str(check.get("status") or "unknown"),
                command=str(check.get("command") or _extract_command(check.get("argv")) or ""),
                target=str(check.get("target") or _extract_target(check.get("argv")) or ""),
                source="quality_gate",
                returncode=_coerce_returncode(check.get("returncode")),
                summary=_redact(str(check.get("summary") or ""))[:700],
                required_for_release=True,
            )
        )
    if not records:
        for check in diagnosis.get("quality_results", []) if isinstance(diagnosis, dict) else []:
            records.append(
                TestEvidenceRecord(
                    name=str(check.get("tool_name") or "quality_check"),
                    status=str(check.get("status") or "unknown"),
                    command=str(check.get("command") or _extract_command(check.get("argv")) or ""),
                    target=str(check.get("target") or "."),
                    source="diagnosis",
                    returncode=_coerce_returncode(check.get("returncode")),
                    summary=_redact(str(check.get("summary") or ""))[:700],
                    required_for_release=True,
                )
            )
    for hint in project_repair.get("regression_hints", []) if isinstance(project_repair, dict) else []:
        key = (str(hint.get("command") or ""), str(hint.get("target") or ""), "regression_hint")
        if any((item.command, item.target, item.source) == key for item in records):
            continue
        records.append(
            TestEvidenceRecord(
                name=str(hint.get("name") or "regression_hint"),
                status="planned",
                command=str(hint.get("command") or ""),
                target=str(hint.get("target") or ""),
                source="project_repair_plan",
                summary=_redact(str(hint.get("reason") or ""))[:500],
                required_for_release=str(hint.get("priority") or "P2").upper() in {"P0", "P1"},
            )
        )
    return records[:80]


def _build_manifest_evidence(delivery_manifest: dict[str, Any]) -> ManifestEvidence:
    if not isinstance(delivery_manifest, dict) or delivery_manifest.get("status") == "empty":
        return ManifestEvidence(
            schema="tiangong.l6_19.delivery_manifest.v1",
            status="empty",
            manifest_available=False,
        )
    release_gate = delivery_manifest.get("release_gate", {}) or {}
    artifacts = [dict(item) for item in delivery_manifest.get("artifacts", []) if isinstance(item, dict)]
    safe_artifacts = []
    for item in artifacts[:30]:
        safe_artifacts.append(
            {
                "path": _clean_path(str(item.get("path") or "")),
                "sha256": str(item.get("sha256") or ""),
                "size": item.get("size", 0),
            }
        )
    return ManifestEvidence(
        schema=str(delivery_manifest.get("schema") or "tiangong.l6_19.delivery_manifest.v1"),
        status="manifest_available",
        release_gate_decision=str(release_gate.get("decision") or "unknown"),
        allow_release=bool(release_gate.get("allow_release", False)),
        payload_files=len(delivery_manifest.get("payload_files", []) or []),
        artifacts=safe_artifacts,
        bundle_sha256=str(delivery_manifest.get("bundle_sha256") or ""),
        manifest_available=True,
    )


def _build_todo_report(
    quality_gate: dict[str, Any],
    test_evidence: list[TestEvidenceRecord],
    manifest_evidence: ManifestEvidence,
    project_repair: dict[str, Any],
    shell_mount: dict[str, Any],
) -> list[TodoItem]:
    todos: list[TodoItem] = []
    decision = str(quality_gate.get("decision") or quality_gate.get("status") or "unknown")
    commands = {item.command for item in test_evidence}
    if "compileall" not in commands:
        todos.append(
            TodoItem(
                "todo_compileall_evidence",
                "P0",
                "补齐 compileall 测试证据。",
                "标准交付证据中缺少 Python 语法层验收。",
                ["S04", "S05"],
            )
        )
    if "pytest" not in commands:
        todos.append(
            TodoItem(
                "todo_pytest_evidence",
                "P1",
                "补齐 pytest 或明确记录未运行原因。",
                "标准交付证据中缺少单元/回归测试验收。",
                ["S04", "S05"],
            )
        )
    if decision in {"fail", "blocked"}:
        todos.append(
            TodoItem(
                "todo_quality_gate_fix",
                "P0",
                "先修复质量门 fail/blocked 项。",
                f"当前质量门 decision={decision}，不应进入正式发布。",
                ["S03", "S04", "S15"],
            )
        )
    if not manifest_evidence.manifest_available:
        todos.append(
            TodoItem(
                "todo_release_manifest",
                "P1",
                "正式发布前生成 L6.19 Release Manifest 与 sha256。",
                "当前只是交付证据标准化报告，未生成正式发布包。",
                ["S05", "S09"],
            )
        )
    sha256_sidecar_present = bool(manifest_evidence.bundle_sha256) or any(str(item.get("path") or "").endswith(".sha256") for item in manifest_evidence.artifacts)
    if not sha256_sidecar_present and manifest_evidence.manifest_available:
        todos.append(
            TodoItem(
                "todo_sha256_sidecar",
                "P1",
                "补齐发布包 sha256 侧车文件。",
                "Manifest 存在但未发现 sha256 侧车证据。",
                ["S05", "S09"],
            )
        )
    if project_repair.get("status") == "empty":
        todos.append(
            TodoItem(
                "todo_repair_plan",
                "P2",
                "生成 L6.25 工程修复计划作为修改清单来源。",
                "ChangeSet 需要 ProjectRadar/PatchPlan/RegressionHint 支撑。",
                ["S02", "S03", "S15"],
            )
        )
    if shell_mount.get("status") == "empty":
        todos.append(
            TodoItem(
                "todo_shell_mount_snapshot",
                "P2",
                "生成 L6.24 十八系统壳装快照。",
                "交付报告需要说明 18 系统当前挂载状态。",
                ["S05", "S09", "S17"],
            )
        )
    todos.append(
        TodoItem(
            "todo_full_pytest",
            "P2",
            "完整 full pytest 未运行时必须保留未做事项。",
            "L6.26 标准化报告只归档本轮证据，不得虚报 full pytest。",
            ["S04", "S05"],
        )
    )
    todos.append(
        TodoItem(
            "todo_gui_windows_installer",
            "P3",
            "GUI / Windows 原生 / 安装包级验收仍需后续执行。",
            "当前阶段主攻交付链标准化，不做桌面端和安装包验收。",
            ["S17", "S18"],
        )
    )
    return _dedupe_todos(todos)


def _release_ready(quality_gate: dict[str, Any], test_evidence: list[TestEvidenceRecord], manifest_evidence: ManifestEvidence) -> bool:
    decision = str(quality_gate.get("decision") or "").lower()
    if decision not in {"pass", "warn"}:
        return False
    commands = {item.command for item in test_evidence if item.status in {"ok", "passed", "pass"}}
    if "compileall" not in commands:
        return False
    return manifest_evidence.manifest_available and manifest_evidence.allow_release


def _build_summary(*, quality_decision: str, release_ready: bool, change_count: int, test_count: int, todo_count: int, notes: str) -> str:
    base = (
        f"已把修改清单、测试证据、Manifest 摘要、完整性摘要和未做事项统一为 L6.26 交付证据；"
        f"change_set={change_count}，test_evidence={test_count}，todo={todo_count}，quality={quality_decision}，release_ready={release_ready}。"
    )
    if notes:
        base += f" 备注：{notes}"
    return base


def _sanitize_audit(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sanitized: list[dict[str, Any]] = []
    for event in events:
        item = {}
        for key in ("event_id", "tool_name", "risk", "status", "summary", "audit_ref"):
            if key in event:
                value = event.get(key)
                item[key] = _redact(str(value)) if isinstance(value, str) else value
        if item:
            sanitized.append(item)
    return sanitized


def _dedupe_todos(todos: list[TodoItem]) -> list[TodoItem]:
    seen: set[str] = set()
    result: list[TodoItem] = []
    for item in todos:
        if item.item_id in seen:
            continue
        seen.add(item.item_id)
        result.append(item)
    return result


def _extract_command(argv: Any) -> str:
    text = " ".join(str(x) for x in argv) if isinstance(argv, list) else str(argv or "")
    lowered = text.lower()
    if "compileall" in lowered:
        return "compileall"
    if "pytest" in lowered:
        return "pytest"
    return ""


def _extract_target(argv: Any) -> str:
    if isinstance(argv, list) and argv:
        return str(argv[-1])
    return ""


def _coerce_returncode(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _clean_path(path: str) -> str:
    cleaned = path.replace("\\", "/").strip()
    cleaned = cleaned.lstrip("/")
    if ".." in cleaned.split("/"):
        return "<redacted-path>"
    return _redact(cleaned)[:260]


def _redact(text: str) -> str:
    result = SENSITIVE_PATTERN.sub(lambda match: f"{match.group(1)}=<redacted>", str(text))
    for word in SENSITIVE_WORDS:
        result = redact_text(result, [word])
    return result


def _stable_digest(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
