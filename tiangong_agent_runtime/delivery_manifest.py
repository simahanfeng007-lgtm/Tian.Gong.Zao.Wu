"""L6.19 产品交付 Manifest 与 Release Bundle 构建器。

该模块把 L6.18 质量门、L6.17 工程诊断、审计摘要与交付 ZIP
归一为标准发布包。它只在工作区内读取/写入，不触碰 tiangong_kernel，
也不绕过 Runtime 的风险分级、PermitGateway、adapter 和审计链。
"""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from dataclasses import dataclass, field, replace
from pathlib import Path
from time import time
from typing import Any

from .audit_bridge import AuditBridge
from .diagnostic_bridge import EngineeringDiagnosticBridge
from .quality_gate_bridge import QualityGateBridge
from .workspace_guard import SENSITIVE_NAMES, SENSITIVE_PARTS, SENSITIVE_SUFFIXES, WorkspaceGuard, WorkspaceViolation

DELIVERY_SCHEMA = "tiangong.l6_19.delivery_manifest.v1"
RELEASE_GATE_SCHEMA = "tiangong.l6_19.release_gate.v1"

EXCLUDE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
}
TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".txt",
    ".toml",
    ".json",
    ".yaml",
    ".yml",
    ".ini",
    ".cfg",
    ".csv",
}
_CONTENT_SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\b(api[_-]?key|secret|token|password|credential)\b\s*[:=]\s*['\"]?[A-Za-z0-9_./+=:-]{16,}"),
]


@dataclass(frozen=True)
class SecretScanFinding:
    path: str
    reason: str
    severity: str = "P0"

    def public_dict(self) -> dict[str, Any]:
        return {"path": self.path, "reason": self.reason, "severity": self.severity}


@dataclass(frozen=True)
class ReleaseGateVerdict:
    schema: str
    decision: str
    allow_release: bool
    reasons: list[str] = field(default_factory=list)

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "decision": self.decision,
            "allow_release": self.allow_release,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class DeliveryManifest:
    schema: str
    generated_at: float
    release_name: str
    baseline: str
    source: str
    target: str
    release_gate: ReleaseGateVerdict
    quality_gate: dict[str, Any]
    diagnosis: dict[str, Any]
    audit_summary: list[dict[str, Any]] = field(default_factory=list)
    secret_scan: dict[str, Any] = field(default_factory=dict)
    payload_files: list[dict[str, Any]] = field(default_factory=list)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    bundle_sha256: str = ""
    bundle_sha256_finalized: bool = False
    notes: list[str] = field(default_factory=list)

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "release_name": self.release_name,
            "baseline": self.baseline,
            "source": self.source,
            "target": self.target,
            "release_gate": self.release_gate.public_dict(),
            "quality_gate": dict(self.quality_gate),
            "diagnosis": dict(self.diagnosis),
            "audit_summary": list(self.audit_summary),
            "secret_scan": dict(self.secret_scan),
            "payload_files": list(self.payload_files),
            "artifacts": list(self.artifacts),
            "bundle_sha256": self.bundle_sha256,
            "bundle_sha256_finalized": self.bundle_sha256_finalized,
            "notes": list(self.notes),
        }

    def markdown_report(self) -> str:
        quality_decision = self.quality_gate.get("decision") or self.quality_gate.get("status")
        findings = self.secret_scan.get("findings", [])
        lines = [
            "# 临渊者 L6.19 标准交付 Manifest",
            "",
            f"- schema: `{self.schema}`",
            f"- release_name: `{self.release_name}`",
            f"- baseline: `{self.baseline}`",
            f"- source: `{self.source}`",
            f"- target: `{self.target}`",
            f"- quality_gate: `{quality_decision}`",
            f"- release_gate: `{self.release_gate.decision}`",
            f"- allow_release: `{self.release_gate.allow_release}`",
            f"- payload_files: `{len(self.payload_files)}`",
            f"- secret_findings: `{len(findings)}`",
            f"- bundle_sha256_finalized: `{self.bundle_sha256_finalized}`",
            "",
            "## Release Gate 原因",
            "",
        ]
        if self.release_gate.reasons:
            for reason in self.release_gate.reasons:
                lines.append(f"- {reason}")
        else:
            lines.append("无阻断原因。")
        lines.extend(["", "## 敏感文件扫描", ""])
        if not findings:
            lines.append("未发现需要阻断发布的敏感文件/凭证路径。")
        for finding in findings[:50]:
            lines.append(f"- [{finding.get('severity')}] `{finding.get('path')}`：{finding.get('reason')}")
        lines.extend(["", "## 产物", ""])
        if not self.artifacts:
            lines.append("未生成发布产物。")
        for artifact in self.artifacts:
            lines.append(
                f"- `{artifact.get('path')}` size={artifact.get('size', 0)} sha256={artifact.get('sha256', '')}"
            )
        if self.notes:
            lines.extend(["", "## 说明", ""])
            for note in self.notes:
                lines.append(f"- {note}")
        lines.append("")
        lines.append("> 本 Manifest 只保存安全摘要、文件哈希和交付裁决，不包含 API Key、完整 prompt 或敏感凭证。")
        return "\n".join(lines)


@dataclass(frozen=True)
class ReleaseBundleBuildResult:
    manifest: DeliveryManifest
    target: Path | None = None
    sha_path: Path | None = None
    manifest_path: Path | None = None
    files_added: int = 0


class DeliveryManifestBridge:
    """保存最近一次 L6.19 交付 Manifest。"""

    def __init__(self) -> None:
        self._last_manifest: DeliveryManifest | None = None

    @property
    def last_manifest(self) -> DeliveryManifest | None:
        return self._last_manifest

    def remember(self, manifest: DeliveryManifest) -> DeliveryManifest:
        self._last_manifest = manifest
        return manifest

    def reset(self) -> None:
        self._last_manifest = None

    def public_dict(self) -> dict[str, Any]:
        if self._last_manifest is None:
            return {"schema": DELIVERY_SCHEMA, "status": "empty", "message": "暂无交付 Manifest，请先执行 /release。"}
        return self._last_manifest.public_dict()

    def export_json(self, path: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return target


class ReleaseBundleBuilder:
    """构建标准 Release Bundle。"""

    def __init__(self, workspace: str | Path) -> None:
        self.guard = WorkspaceGuard(workspace)

    def build(
        self,
        *,
        source: str | Path,
        target: str | Path,
        release_name: str,
        baseline: str,
        quality_gate: dict[str, Any],
        diagnosis: dict[str, Any],
        audit_summary: list[dict[str, Any]],
        manifest_path: str | Path | None = None,
    ) -> ReleaseBundleBuildResult:
        source_path = self.guard.resolve_for_read(source)
        target_path = self.guard.resolve_for_artifact(target)
        if not source_path.exists():
            raise WorkspaceViolation(f"发布源不存在：{source}")
        if source_path.is_file():
            base_dir = source_path.parent
            candidate_files = [source_path]
        else:
            base_dir = source_path
            candidate_files = [item for item in source_path.rglob("*") if item.is_file()]

        findings = scan_for_secret_findings(candidate_files, base_dir=base_dir, workspace=self.guard.workspace)
        payload_files = _collect_payload_files(
            candidate_files,
            base_dir=base_dir,
            workspace=self.guard.workspace,
            excluded_paths={target_path, target_path.with_suffix(target_path.suffix + ".sha256")},
        )
        gate = evaluate_release_gate(quality_gate, findings)
        manifest_target = self.guard.resolve_for_artifact(manifest_path) if manifest_path else target_path.with_suffix(target_path.suffix + ".manifest.json")
        manifest = DeliveryManifest(
            schema=DELIVERY_SCHEMA,
            generated_at=time(),
            release_name=release_name,
            baseline=baseline,
            source=_relative(source_path, self.guard.workspace),
            target=_relative(target_path, self.guard.workspace),
            release_gate=gate,
            quality_gate=quality_gate,
            diagnosis=diagnosis,
            audit_summary=audit_summary[-50:],
            secret_scan={
                "schema": "tiangong.l6_19.secret_scan.v1",
                "scanned_files": len(candidate_files),
                "packable_files": len(payload_files),
                "findings": [finding.public_dict() for finding in findings],
            },
            payload_files=payload_files[:5000],
            notes=[
                "ZIP 内 Manifest 无法自包含最终 ZIP 自身 SHA256；最终 SHA256 写入侧车 Manifest 与 .sha256 文件。",
                "quality_gate 为 fail/blocked 或发现敏感文件时，Release Gate 阻断发布包生成。",
            ],
        )
        if not gate.allow_release:
            manifest_target.write_text(json.dumps(manifest.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
            return ReleaseBundleBuildResult(manifest=manifest, manifest_path=manifest_target)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        files_added = 0
        with zipfile.ZipFile(target_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("RELEASE_MANIFEST.json", json.dumps(manifest.public_dict(), ensure_ascii=False, indent=2))
            zf.writestr("RELEASE_MANIFEST.md", manifest.markdown_report())
            zf.writestr("reports/quality_gate.json", json.dumps(quality_gate, ensure_ascii=False, indent=2))
            zf.writestr("reports/diagnosis.json", json.dumps(diagnosis, ensure_ascii=False, indent=2))
            zf.writestr("reports/audit_summary.json", json.dumps(audit_summary[-50:], ensure_ascii=False, indent=2))
            for record in payload_files:
                path = self.guard.workspace / record["workspace_path"]
                if not path.exists() or not path.is_file():
                    continue
                zf.write(path, f"payload/{record['relative_path']}")
                files_added += 1

        bundle_sha256 = hashlib.sha256(target_path.read_bytes()).hexdigest()
        sha_path = target_path.with_suffix(target_path.suffix + ".sha256")
        sha_path.write_text(f"{bundle_sha256}  {target_path.name}\n", encoding="utf-8")
        artifacts = [
            {"path": _relative(target_path, self.guard.workspace), "sha256": bundle_sha256, "size": target_path.stat().st_size},
            {"path": _relative(sha_path, self.guard.workspace), "sha256": _sha256_file(sha_path), "size": sha_path.stat().st_size},
        ]
        finalized = replace(
            manifest,
            artifacts=artifacts,
            bundle_sha256=bundle_sha256,
            bundle_sha256_finalized=True,
        )
        manifest_target.write_text(json.dumps(finalized.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return ReleaseBundleBuildResult(
            manifest=finalized,
            target=target_path,
            sha_path=sha_path,
            manifest_path=manifest_target,
            files_added=files_added,
        )


def evaluate_release_gate(quality_gate: dict[str, Any], findings: list[SecretScanFinding]) -> ReleaseGateVerdict:
    reasons: list[str] = []
    if not quality_gate or quality_gate.get("status") == "empty":
        reasons.append("缺少 L6.18 质量门裁决，禁止发布。")
        return ReleaseGateVerdict(RELEASE_GATE_SCHEMA, "blocked", False, reasons)

    decision = str(quality_gate.get("decision") or "").lower()
    allow_package = bool(quality_gate.get("allow_package", False))
    if decision in {"blocked", "fail"} or not allow_package:
        reasons.append(f"质量门 decision={decision or '<missing>'}, allow_package={allow_package}，Release Gate 阻断。")
    if findings:
        reasons.append(f"Forbidden/Secret Scan 发现 {len(findings)} 个敏感文件或凭证信号，禁止生成发布包。")
    if reasons:
        return ReleaseGateVerdict(RELEASE_GATE_SCHEMA, "blocked", False, reasons)
    if decision == "warn":
        return ReleaseGateVerdict(
            RELEASE_GATE_SCHEMA,
            "warn",
            True,
            ["质量门为 warn：允许受控发布，但 Manifest 必须披露 P2 警告。"],
        )
    return ReleaseGateVerdict(RELEASE_GATE_SCHEMA, "pass", True, ["质量门允许发布，敏感扫描未发现阻断项。"])


def build_create_release_bundle_adapter(
    delivery_bridge: DeliveryManifestBridge,
    quality_gate_bridge: QualityGateBridge,
    diagnostics: EngineeringDiagnosticBridge,
    audit: AuditBridge,
):
    def create_release_bundle_adapter(invocation, context):
        from .tool_result import ToolResult, ToolResultStatus

        try:
            builder = ReleaseBundleBuilder(context.workspace)
            result = builder.build(
                source=invocation.arguments.get("source") or ".",
                target=invocation.arguments.get("target") or "dist/l6_19_release_bundle.zip",
                release_name=str(invocation.arguments.get("release_name") or "linyuanzhe_l6_19_release"),
                baseline=str(invocation.arguments.get("baseline") or "L6.18-quality-gate"),
                quality_gate=quality_gate_bridge.public_dict(),
                diagnosis=diagnostics.public_dict(),
                audit_summary=audit.recent_summary(),
                manifest_path=invocation.arguments.get("manifest_path") or None,
            )
            delivery_bridge.remember(result.manifest)
            manifest_rel = _relative(result.manifest_path, Path(context.workspace).resolve()) if result.manifest_path else ""
            if not result.manifest.release_gate.allow_release:
                return ToolResult(
                    step_id=invocation.step_id,
                    tool_name=invocation.tool_name,
                    status=ToolResultStatus.BLOCKED,
                    output_summary="Release Gate 阻断：" + "; ".join(result.manifest.release_gate.reasons),
                    error_code="release_gate_blocked",
                    artifacts=[manifest_rel] if manifest_rel else [],
                    data=result.manifest.public_dict(),
                )
            artifacts = [
                _relative(result.target, Path(context.workspace).resolve()) if result.target else "",
                _relative(result.sha_path, Path(context.workspace).resolve()) if result.sha_path else "",
                manifest_rel,
            ]
            artifacts = [item for item in artifacts if item]
            return ToolResult(
                step_id=invocation.step_id,
                tool_name=invocation.tool_name,
                status=ToolResultStatus.OK,
                output_summary=(
                    f"L6.19 Release Bundle 已生成：{artifacts[0] if artifacts else '<unknown>'}；"
                    f"files={result.files_added}；sha256={result.manifest.bundle_sha256}；"
                    f"release_gate={result.manifest.release_gate.decision}"
                ),
                artifacts=artifacts,
                data=result.manifest.public_dict(),
            )
        except WorkspaceViolation as exc:
            return ToolResult(
                step_id=invocation.step_id,
                tool_name=invocation.tool_name,
                status=ToolResultStatus.BLOCKED,
                output_summary=str(exc),
                error_code="workspace_violation",
            )
        except OSError as exc:
            return ToolResult(
                step_id=invocation.step_id,
                tool_name=invocation.tool_name,
                status=ToolResultStatus.FAILED,
                output_summary=f"Release Bundle 构建失败：{exc}",
                error_code="release_bundle_failed",
            )

    return create_release_bundle_adapter


def scan_for_secret_findings(files: list[Path], *, base_dir: Path, workspace: Path) -> list[SecretScanFinding]:
    findings: list[SecretScanFinding] = []
    for path in files:
        rel = _relative(path, workspace)
        path_reason = _sensitive_path_reason(path)
        if path_reason:
            findings.append(SecretScanFinding(rel, path_reason))
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            if path.stat().st_size > 256_000:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")[:64_000]
        except OSError:
            continue
        for pattern in _CONTENT_SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(SecretScanFinding(rel, "文本内容疑似包含凭证、Token、密码或私钥。"))
                break
    return findings


def _collect_payload_files(
    files: list[Path],
    *,
    base_dir: Path,
    workspace: Path,
    excluded_paths: set[Path],
) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    excluded_resolved = {path.resolve() for path in excluded_paths}
    for path in sorted(files, key=lambda item: _relative(item, base_dir)):
        resolved = path.resolve()
        if resolved in excluded_resolved:
            continue
        if _is_excluded(path):
            continue
        if _sensitive_path_reason(path):
            continue
        rel_to_source = _relative(path, base_dir)
        rel_to_workspace = _relative(path, workspace)
        try:
            stat = path.stat()
            payload.append(
                {
                    "relative_path": rel_to_source,
                    "workspace_path": rel_to_workspace,
                    "size": stat.st_size,
                    "sha256": _sha256_file(path),
                }
            )
        except OSError:
            continue
    return payload


def _is_excluded(path: Path) -> bool:
    return bool({part.lower() for part in path.parts}.intersection(EXCLUDE_DIRS))


def _sensitive_path_reason(path: Path) -> str:
    lowered_parts = {part.lower() for part in path.parts}
    if path.name.lower() in SENSITIVE_NAMES:
        return f"敏感文件名：{path.name}"
    if path.suffix.lower() in SENSITIVE_SUFFIXES:
        return f"敏感后缀：{path.suffix}"
    if lowered_parts.intersection(SENSITIVE_PARTS):
        return "敏感目录或凭证路径。"
    lowered = path.as_posix().lower()
    if any(term in lowered for term in ["secret", "token", "credential", "api_key"]):
        return "路径名疑似包含 secret/token/credential/api_key。"
    return ""


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _relative(path: Path | None, base: Path) -> str:
    if path is None:
        return ""
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return path.name
