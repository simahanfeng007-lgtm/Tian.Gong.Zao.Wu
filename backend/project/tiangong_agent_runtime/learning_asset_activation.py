"""L6.70.2-R20 active Tool/Skill registration after learning success.

R16-R19 turn autonomous learning / experience summaries into normalized contracts,
reviewable candidate packages and a lightweight release gate. R20 closes the
execution gap: when the release gate is ready, the candidate is promoted into a
workspace-scoped active asset registry and Tool assets are registered into the
current RuntimeToolRegistry as callable learned_* Runtime tools.

Boundary: activation is still governed by Runtime risk/audit. It writes only
under ``.linyuanzhe/active_assets/r20`` in the current workspace, registers only
clean learned_* handles, never imports/copies v1, never monkey-patches existing
Runtime tools, never starts background loops and never replaces the LLM as final
decider. Rollback is deleting/disabling the active record and reloading registry.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import re
import shutil
from pathlib import Path
from time import time
from typing import Any

from tiangong_agent_shell.safe_logging import redact_text

from .runtime_tool_registry import RuntimeToolRegistry, ToolDescriptor
from .tool_invocation import ToolInvocation
from .tool_result import ToolResult, ToolResultStatus
from .turn_context import TurnContext
from .workspace_guard import WorkspaceGuard, WorkspaceViolation

ACTIVATION_SCHEMA = "tiangong.l6702.r20.learning_asset_activation.v1"
ACTIVE_ROOT = ".linyuanzhe/active_assets/r20"
ACTIVE_REGISTRY_FILE = "active_assets_registry.json"

def _active_asset_state_root(workspace: str | Path, *, for_write: bool = False) -> Path:
    """Return the active-asset registry root without polluting broad host workspaces.

    Desktop/real-host runs may use a tool workspace such as "/" or a user home.
    Loading active assets is a read-side bootstrap and must not mkdir
    ``<workspace>/.linyuanzhe``.  When the bridge provides LINYUANZHE_STATE_DIR /
    TIANGONG_STATE_DIR, runtime state is redirected there.
    """
    override = os.environ.get("LINYUANZHE_STATE_DIR") or os.environ.get("TIANGONG_STATE_DIR")
    if override:
        root = Path(override).expanduser().resolve() / ACTIVE_ROOT.replace(".linyuanzhe/", "")
        if for_write:
            root.mkdir(parents=True, exist_ok=True)
        return root
    guard = WorkspaceGuard(workspace)
    return guard.resolve_for_artifact(ACTIVE_ROOT) if for_write else guard.resolve_for_read(ACTIVE_ROOT)

ACTIVATION_TOOL_NAMES = {
    "learning_asset_activation_guide",
    "learning_asset_activation_apply",
    "learning_asset_activation_status",
    "learning_asset_activation_smoke",
}

SENSITIVE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer|token|secret|password|credential)\s*[:=]\s*[^\s,;]+"
)
FORBIDDEN_ACTIVE_PATTERNS = {
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


def build_activation_guide() -> dict[str, Any]:
    return {
        "schema": ACTIVATION_SCHEMA,
        "purpose": "R20：学习成功后，把通过 R19 的候选 Tool/Skill 受控注册为 workspace 级 active asset，并让 learned_* Tool 立即可调用。",
        "commands": {
            "guide": "asset-activate guide",
            "apply": "asset-activate apply",
            "status": "asset-activate status",
            "smoke": "asset-activate smoke",
            "drill": "asset-activate drill pytest missing tests",
            "call": "runtime-tools tool <learned_tool_name> {json_args}",
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
            "learning_asset_release_gate_check",
            "learning_asset_activation_apply",
            "learning_asset_activation_smoke",
            "runtime_tool_alignment_check",
        ],
        "execution_first_policy": {
            "after_learning_success": "通过 R16/R17/R18/R19 后直接进入 R20 受控激活。",
            "tool_handle": "Tool 候选注册为 learned_tool_*，可经 runtime-tools tool 或模型计划直接调用。",
            "skill_handle": "Skill 候选写入 active skill registry，并同时暴露 learned_skill_* 指南工具。",
            "rollback": "删除/禁用 active_assets_registry 对应记录并重载 Runtime；候选包原始证据保留。",
        },
        "hard_boundaries": {
            "may_write": [
                ".linyuanzhe/active_assets/r20/<asset>/",
                ".linyuanzhe/active_assets/r20/active_assets_registry.json",
            ],
            "may_register": ["learned_tool_*", "learned_skill_*"],
            "must_not": [
                "overwrite built-in Runtime tools",
                "write outside workspace",
                "import/copy v1",
                "reuse v1 registry/executor/provider/self-iteration",
                "monkey patch existing code",
                "start background loop",
                "read credentials",
            ],
        },
    }


class LearningAssetActivationBridge:
    """Promote review-ready candidate packages into active learned assets."""

    def __init__(self, registry: RuntimeToolRegistry) -> None:
        self.registry = registry
        self._last_report: dict[str, Any] | None = None
        self._loaded_registry_paths: set[str] = set()

    @property
    def last_report(self) -> dict[str, Any] | None:
        return self._last_report

    def guide(self) -> dict[str, Any]:
        return build_activation_guide()

    def apply(
        self,
        *,
        workspace: str | Path,
        release_gate_report: dict[str, Any],
        candidate_report: dict[str, Any],
        notes: str = "",
    ) -> dict[str, Any]:
        guard = WorkspaceGuard(workspace)
        root = _active_asset_state_root(guard.workspace, for_write=True)
        root.mkdir(parents=True, exist_ok=True)
        registry_path = root / ACTIVE_REGISTRY_FILE
        existing = _read_active_registry(registry_path)
        records: list[dict[str, Any]] = [item for item in existing.get("records", []) if isinstance(item, dict)]
        issues: list[dict[str, str]] = []

        if release_gate_report.get("status") != "registration_request_ready":
            issues.append(_issue("release_gate.status", "P1", "R19 必须达到 registration_request_ready。", str(release_gate_report.get("status") or "empty")))
        registration_request = release_gate_report.get("registration_request") if isinstance(release_gate_report.get("registration_request"), dict) else {}
        if registration_request.get("ready") is not True:
            issues.append(_issue("registration_request.ready", "P1", "注册申请未 ready，拒绝激活。"))
        packages = [item for item in _as_list(candidate_report.get("packages")) if isinstance(item, dict)]
        if not packages:
            issues.append(_issue("candidate.packages", "P1", "没有可激活候选包。"))

        activated: list[dict[str, Any]] = []
        existing_by_key = {_record_key(item): item for item in records}
        for package in packages:
            try:
                record = self._activate_package(guard=guard, root=root, package=package, notes=notes)
                existing_by_key[_record_key(record)] = record
                activated.append(record)
            except (OSError, ValueError, WorkspaceViolation) as exc:
                issues.append(_issue("activation.package", "P1", f"候选包激活失败：{exc}", str(package.get("package_ref") or "")))

        records = sorted(existing_by_key.values(), key=lambda item: str(item.get("tool_name") or item.get("asset_ref") or ""))
        status = "active" if activated and not any(item.get("severity") in {"P0", "P1"} for item in issues) else "blocked"
        payload = {
            "schema": ACTIVATION_SCHEMA,
            "generated_at": time(),
            "status": status,
            "workspace_root": str(guard.workspace),
            "active_root": str(root),
            "registry_path": str(registry_path),
            "active_count": len(records),
            "activated_count": len(activated),
            "records": records,
            "activated_assets": activated,
            "issues": issues,
            "issue_count": len(issues),
            "chain": build_activation_guide()["canonical_pipeline"],
            "notes": _safe_text(notes, limit=400),
            "no_pollution_assertions": _no_pollution_assertions(),
            "next_action_hint": {
                "next_tool": "learning_asset_activation_smoke" if status == "active" else "learning_asset_release_gate_check",
                "reason": "激活成功后必须立刻 smoke 调用 learned_*，再跑 runtime_tool_alignment_check。",
                "llm_final_decision_required": True,
            },
        }
        _write_json(registry_path, _relocatable_registry_payload({k: v for k, v in payload.items() if k not in {"activated_assets", "issues", "issue_count", "chain", "notes", "next_action_hint"}}, workspace=guard.workspace, active_root=root, registry_path=registry_path))
        self._loaded_registry_paths.discard(str(registry_path))
        self.load_active_assets(workspace=workspace, force=True)
        self._last_report = payload
        return payload

    def status(self, *, workspace: str | Path) -> dict[str, Any]:
        report = self.load_active_assets(workspace=workspace, force=True)
        self._last_report = report
        return report

    def smoke(self, *, workspace: str | Path, sample_args: dict[str, Any] | None = None) -> dict[str, Any]:
        status_report = self.load_active_assets(workspace=workspace, force=True)
        sample = sample_args if isinstance(sample_args, dict) else {"query": "r20 activation smoke", "goal": "verify learned asset callable"}
        results: list[dict[str, Any]] = []
        issues: list[dict[str, str]] = []
        for record in status_report.get("records", []):
            if not isinstance(record, dict):
                continue
            try:
                record_sample = _sample_args_for_active_record(record, sample)
                call = _call_active_record(record, record_sample, workspace=Path(workspace).resolve())
                results.append({
                    "tool_name": record.get("tool_name"),
                    "asset_kind": record.get("asset_kind"),
                    "ok": call.get("status") in {"ok", "pass"},
                    "output_summary": call.get("output_summary"),
                    "data_keys": sorted((call.get("data") or {}).keys()) if isinstance(call.get("data"), dict) else [],
                })
            except (OSError, ValueError, WorkspaceViolation) as exc:
                issues.append(_issue("smoke.call", "P1", f"active asset smoke 失败：{exc}", str(record.get("tool_name") or "")))
        ok = bool(results) and all(item.get("ok") for item in results) and not issues
        report = {
            "schema": ACTIVATION_SCHEMA,
            "generated_at": time(),
            "status": "pass" if ok else ("empty" if not results else "needs_review"),
            "workspace_root": status_report.get("workspace_root"),
            "active_count": status_report.get("active_count", 0),
            "smoke_count": len(results),
            "smoke_results": results,
            "issues": issues,
            "issue_count": len(issues),
            "next_action_hint": {
                "next_tool": "runtime_tool_alignment_check" if ok else "learning_asset_activation_status",
                "reason": "smoke 通过后验证 learned_* 已纳入全局 usage card / 风险 / 路由对齐。",
            },
        }
        self._last_report = report
        return report

    def public_dict(self) -> dict[str, Any]:
        return self._last_report or {"schema": ACTIVATION_SCHEMA, "status": "empty", "message": "暂无 R20 active asset 报告。"}

    def build_planner_hint(self) -> str:
        if not self._last_report:
            return ""
        return f"最近 R20 学习资产激活：status={self._last_report.get('status')}; active_count={self._last_report.get('active_count', 0)}"

    def load_active_assets(self, *, workspace: str | Path, force: bool = False) -> dict[str, Any]:
        guard = WorkspaceGuard(workspace)
        root = _active_asset_state_root(workspace, for_write=False)
        registry_path = root / ACTIVE_REGISTRY_FILE
        if not registry_path.exists():
            report = {
                "schema": ACTIVATION_SCHEMA,
                "generated_at": time(),
                "status": "empty",
                "workspace_root": str(guard.workspace),
                "active_root": str(root),
                "registry_path": str(registry_path),
                "active_count": 0,
                "records": [],
                "issues": [],
                "issue_count": 0,
                "next_action_hint": {"next_tool": "learning_asset_activation_apply", "reason": "尚无 active asset。"},
            }
            self._last_report = report
            return report

        payload = _read_active_registry(registry_path)
        raw_records = _active_records(payload)
        records, relocation_issues, relocated_count, changed = _relocate_active_records(
            raw_records, workspace=guard.workspace, active_root=root
        )
        previous_relocated_count = int(payload.get("relocated_count") or 0) if isinstance(payload.get("relocated_count"), int) else 0
        relocated_count = max(relocated_count, previous_relocated_count)
        payload = dict(payload)
        payload.update({
            "schema": ACTIVATION_SCHEMA,
            "status": "active" if records else "empty",
            "workspace_root": str(guard.workspace),
            "active_root": str(root),
            "registry_path": str(registry_path),
            "active_count": len(records),
            "records": records,
            "path_mode": "workspace_relative_relocatable",
            "relocation_supported": True,
            "relocated_count": relocated_count,
        })
        _write_json(registry_path, _relocatable_registry_payload(payload, workspace=guard.workspace, active_root=root, registry_path=registry_path))
        if changed:
            self._loaded_registry_paths.discard(str(registry_path))

        if force or changed or str(registry_path) not in self._loaded_registry_paths:
            for record in records:
                self._register_active_record(record)
            self._loaded_registry_paths.add(str(registry_path))

        status = "active" if records and not relocation_issues else ("active_with_issues" if records else "empty")
        report = {
            "schema": ACTIVATION_SCHEMA,
            "generated_at": time(),
            "status": status,
            "workspace_root": str(guard.workspace),
            "active_root": str(root),
            "registry_path": str(registry_path),
            "active_count": len(records),
            "records": records,
            "issues": relocation_issues,
            "issue_count": len(relocation_issues),
            "path_mode": "workspace_relative_relocatable",
            "relocation_supported": True,
            "relocated_count": relocated_count,
            "no_pollution_assertions": _no_pollution_assertions(),
            "next_action_hint": {"next_tool": "learning_asset_activation_smoke" if records else "learning_asset_activation_apply"},
        }
        self._last_report = report
        return report

    def _activate_package(self, *, guard: WorkspaceGuard, root: Path, package: dict[str, Any], notes: str) -> dict[str, Any]:
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
                    raise ValueError("候选包 candidate_only 必须为 True。")
            elif value is True:
                raise ValueError(f"候选包越界字段为 True：{flag}")
        if package.get("status") != "review_ready":
            raise ValueError("候选包必须为 review_ready。")
        if package.get("static_scan_status") != "pass" or package.get("smoke_status") != "pass":
            raise ValueError("候选包静态扫描和 smoke 必须均为 pass。")

        package_dir = guard.resolve_for_read(str(package.get("package_dir") or ""))
        manifest_path = guard.resolve_for_read(str(package.get("manifest_path") or package_dir / "manifest.json"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        _assert_manifest_clean(manifest)
        _scan_text_files(package_dir)
        kind = _safe_text(manifest.get("asset_kind"), limit=40)
        if kind not in {"tool", "skill"}:
            raise ValueError(f"R20 只激活 tool/skill，当前 asset_kind={kind}")
        name = _slug_name(manifest.get("name") or package.get("name") or kind)
        digest = hashlib.sha256(str(manifest.get("asset_ref") or package.get("package_ref") or name).encode("utf-8")).hexdigest()[:10]
        active_dir = root / f"{kind}_{name}_{digest}"
        if active_dir.exists():
            shutil.rmtree(active_dir)
        shutil.copytree(package_dir, active_dir)
        tool_name = _tool_name(kind=kind, name=name, digest=digest)
        if tool_name in self.registry.names() and not tool_name.startswith(("learned_tool_", "learned_skill_")):
            raise ValueError(f"拒绝覆盖内置工具：{tool_name}")
        activation_manifest = {
            "schema": ACTIVATION_SCHEMA,
            "activated_at": time(),
            "status": "active",
            "asset_ref": _safe_text(manifest.get("asset_ref"), limit=220),
            "asset_kind": kind,
            "name": name,
            "version": _safe_text(manifest.get("version"), limit=80) or "0.1.0-active",
            "tool_name": tool_name,
            "descriptor_risk": "A3",
            "purpose": _safe_text(manifest.get("purpose"), limit=900),
            "usage_card": manifest.get("usage_card") if isinstance(manifest.get("usage_card"), dict) else {},
            "chain_recipe": _as_list(manifest.get("chain_recipe"))[:20],
            "adapter_template_schema": _safe_text(manifest.get("adapter_template_schema"), limit=160),
            "adapter_template_id": _safe_text(manifest.get("adapter_template_id"), limit=120),
            "source_package_ref": _safe_text(package.get("package_ref"), limit=220),
            "source_package_dir": str(package_dir),
            "source_package_dir_relative": _relative_to_workspace(package_dir, guard.workspace),
            "active_dir": str(active_dir),
            "active_dir_relative": _relative_to_workspace(active_dir, guard.workspace),
            "active_manifest_path": str(active_dir / "activation_manifest.json"),
            "active_manifest_relative": _relative_to_workspace(active_dir / "activation_manifest.json", guard.workspace),
            "source_manifest_path": str(manifest_path),
            "source_manifest_relative": _relative_to_workspace(manifest_path, guard.workspace),
            "rollback_evidence_path": str(active_dir / "rollback_evidence.json"),
            "rollback_evidence_relative": _relative_to_workspace(active_dir / "rollback_evidence.json", guard.workspace),
            "registration_review_path": str(active_dir / "registration_review.json"),
            "registration_review_relative": _relative_to_workspace(active_dir / "registration_review.json", guard.workspace),
            "callable_now": True,
            "runtime_registered_now": True,
            "skill_active_now": kind == "skill",
            "llm_is_final_decider": True,
            "no_pollution_assertions": _no_pollution_assertions(),
            "notes": _safe_text(notes, limit=400),
        }
        _write_json(active_dir / "activation_manifest.json", _relocatable_record(activation_manifest, workspace=guard.workspace))
        record = dict(activation_manifest)
        self._register_active_record(record)
        return record

    def _register_active_record(self, record: dict[str, Any]) -> None:
        tool_name = _safe_text(record.get("tool_name"), limit=160)
        if not tool_name.startswith(("learned_tool_", "learned_skill_")):
            raise ValueError(f"active asset tool_name 必须使用 learned_* 前缀：{tool_name}")
        if tool_name in {"learning_asset_activation_apply", "learning_asset_activation_status", "learning_asset_activation_smoke"}:
            raise ValueError("active asset 不得覆盖 R20 激活工具。")
        description = _safe_text(record.get("purpose"), limit=240) or "R20 active learned asset callable by Runtime."
        self.registry.register(
            ToolDescriptor(tool_name, f"R20 已激活学习资产：{description}", "A3"),
            _build_active_asset_adapter(record),
        )


def build_learning_asset_activation_guide_adapter():
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary="R20 学习资产激活指南已生成：学习成功后可注册 learned_* 并立即 smoke 调用。",
            data=build_activation_guide(),
        )
    return adapter


def build_learning_asset_activation_apply_adapter(bridge: LearningAssetActivationBridge, release_gate: Any, candidate_sandbox: Any):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            report = bridge.apply(
                workspace=context.workspace,
                release_gate_report=release_gate.public_dict(),
                candidate_report=candidate_sandbox.public_dict(),
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
            )
        except (TypeError, ValueError, OSError) as exc:
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.FAILED,
                f"R20 学习资产激活失败：{exc}",
                error_code="learning_asset_activation_apply_failed",
            )
        status = ToolResultStatus.OK if report.get("status") == "active" else ToolResultStatus.FAILED
        artifacts = [str(item.get("active_dir")) for item in report.get("activated_assets", []) if isinstance(item, dict)]
        if report.get("registry_path"):
            artifacts.append(str(report["registry_path"]))
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=status,
            output_summary=(
                f"R20 学习资产激活：status={report.get('status')}；activated={report.get('activated_count', 0)}；"
                f"active_total={report.get('active_count', 0)}；issues={report.get('issue_count', 0)}。"
            ),
            data=report,
            artifacts=artifacts,
            error_code="" if status is ToolResultStatus.OK else "learning_asset_activation_blocked",
        )
    return adapter


def build_learning_asset_activation_status_adapter(bridge: LearningAssetActivationBridge):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            report = bridge.status(workspace=context.workspace)
        except (TypeError, ValueError, OSError) as exc:
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"R20 active asset 状态读取失败：{exc}", error_code="learning_asset_activation_status_failed")
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=f"R20 active asset 状态：status={report.get('status')}；active_count={report.get('active_count', 0)}。",
            data=report,
            artifacts=[report.get("registry_path", "")] if report.get("registry_path") else [],
        )
    return adapter


def build_learning_asset_activation_smoke_adapter(bridge: LearningAssetActivationBridge):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        raw_args = invocation.arguments.get("sample_args")
        sample_args = raw_args if isinstance(raw_args, dict) else None
        try:
            report = bridge.smoke(workspace=context.workspace, sample_args=sample_args)
        except (TypeError, ValueError, OSError) as exc:
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"R20 active asset smoke 失败：{exc}", error_code="learning_asset_activation_smoke_failed")
        status = ToolResultStatus.OK if report.get("status") == "pass" else ToolResultStatus.FAILED
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=status,
            output_summary=f"R20 active asset smoke：status={report.get('status')}；smoke_count={report.get('smoke_count', 0)}；issues={report.get('issue_count', 0)}。",
            data=report,
            error_code="" if status is ToolResultStatus.OK else "learning_asset_activation_smoke_needs_review",
        )
    return adapter


def _build_active_asset_adapter(record: dict[str, Any]):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            payload = _call_active_record(record, invocation.arguments, workspace=context.workspace)
        except (OSError, ValueError, WorkspaceViolation) as exc:
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.FAILED,
                f"active learned asset 调用失败：{exc}",
                error_code="active_learned_asset_call_failed",
            )
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK if payload.get("status") in {"ok", "pass"} else ToolResultStatus.FAILED,
            output_summary=str(payload.get("output_summary") or "R20 active learned asset called."),
            data=payload,
            artifacts=[str(record.get("active_dir"))] if record.get("active_dir") else [],
            error_code="" if payload.get("status") in {"ok", "pass"} else "active_learned_asset_returned_non_ok",
        )
    return adapter



def _sample_args_for_active_record(record: dict[str, Any], default: dict[str, Any]) -> dict[str, Any]:
    """Return template-specific smoke args for R21 learned adapters while preserving R20 defaults."""
    sample = dict(default or {})
    template_id = _safe_text(record.get("adapter_template_id"), limit=120)
    if template_id == "pure_transform":
        return {"operation": "simple_stats", "items": [1, 2, 3, 5], "query": sample.get("query") or "r21 activation smoke"}
    if template_id == "schema_contract_check":
        return {
            "schema_type": "usage_card",
            "payload": {
                "when_to_use": "verify learned adapter smoke",
                "how_to_call": "runtime-tools tool <learned_tool_name> {json_args}",
                "do_not_use_when": "requires network shell credential or autonomous writes",
                "next_action_hint": "run runtime_tool_alignment_check",
            },
        }
    if template_id == "project_diagnostic":
        return {
            "log_text": "ImportError: cannot import name add from src.calc\nFAILED tests/test_calc.py",
            "changed_files": ["src/calc.py", "tests/test_calc.py"],
            "goal": "diagnose failure summary",
        }
    if template_id == "doc_skill_production":
        return {
            "operation": "usage_card",
            "title": "R21 activation smoke",
            "goal": "verify learned adapter callable",
            "evidence": ["activation smoke", "runtime callable"],
        }
    if template_id == "experience_reuse":
        return {
            "digests": ["pytest failed then import error fixed", "usage card missing field was corrected"],
            "goal": "reuse learned adapter experience",
        }
    return sample

def _call_active_record(record: dict[str, Any], arguments: dict[str, Any], *, workspace: str | Path | None = None) -> dict[str, Any]:
    active_value = _safe_text(record.get("active_dir") or record.get("active_dir_relative"), limit=1000)
    if not active_value:
        raise ValueError("active_dir 缺失。")
    raw_active = Path(active_value).expanduser()
    if raw_active.is_absolute():
        active_dir = raw_active.resolve()
    else:
        base = Path(workspace).resolve() if workspace is not None else Path.cwd().resolve()
        active_dir = (base / raw_active).resolve()
    if not active_dir.exists():
        raise ValueError(f"active_dir 不存在：{active_dir}")
    _scan_text_files(active_dir)
    manifest_path = active_dir / "activation_manifest.json"
    if not manifest_path.exists():
        raise ValueError("active asset 缺少 activation_manifest.json。")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    asset_kind = str(manifest.get("asset_kind") or record.get("asset_kind") or "")
    base_data = {
        "active_asset": {
            "asset_ref": manifest.get("asset_ref"),
            "asset_kind": manifest.get("asset_kind"),
            "name": manifest.get("name"),
            "tool_name": manifest.get("tool_name"),
            "version": manifest.get("version"),
            "purpose": manifest.get("purpose"),
        },
        "arguments": dict(arguments or {}),
        "usage_card": manifest.get("usage_card") if isinstance(manifest.get("usage_card"), dict) else {},
        "chain_recipe": _as_list(manifest.get("chain_recipe")),
        "next_action_hint": {
            "next_tool": "runtime_tool_alignment_check",
            "reason": "learned_* 已可调用；LLM 根据 usage_card 与 chain_recipe 继续选择实际执行链或沉淀 handoff。",
            "llm_final_decision_required": True,
        },
    }
    if asset_kind == "tool":
        adapter_path = active_dir / "tool_adapter_draft.py"
        if adapter_path.exists():
            candidate_output = _execute_candidate_adapter(adapter_path, arguments)
            status = str(candidate_output.get("status") or "ok")
            base_data.update({
                "call_mode": "activated_candidate_adapter",
                "candidate_adapter_path": str(adapter_path),
                "candidate_output": candidate_output,
            })
            return {
                "schema": ACTIVATION_SCHEMA,
                "status": status,
                "output_summary": str(candidate_output.get("output_summary") or f"已执行 R20 active learned tool：{manifest.get('tool_name')}。"),
                "data": base_data,
            }
    if asset_kind == "skill":
        skill_path = active_dir / "SKILL.md"
        skill_text = skill_path.read_text(encoding="utf-8", errors="ignore") if skill_path.exists() else ""
        base_data.update({
            "call_mode": "active_skill_card",
            "skill_path": str(skill_path) if skill_path.exists() else "",
            "skill_excerpt": skill_text[:2400],
        })
    else:
        base_data.update({"call_mode": "active_asset_manifest"})
    return {
        "schema": ACTIVATION_SCHEMA,
        "status": "ok",
        "output_summary": f"已调用 R20 active learned asset：{manifest.get('tool_name')} / {manifest.get('name')}。",
        "data": base_data,
    }


def _execute_candidate_adapter(adapter_path: Path, arguments: dict[str, Any]) -> dict[str, Any]:
    text = adapter_path.read_text(encoding="utf-8", errors="ignore")
    _scan_candidate_adapter_ast(text, adapter_path)
    module_name = f"_linyuanzhe_active_{hashlib.sha256(str(adapter_path).encode('utf-8')).hexdigest()[:16]}"
    spec = importlib.util.spec_from_file_location(module_name, adapter_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"无法加载 active learned tool adapter：{adapter_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fn = getattr(module, "candidate_adapter_draft", None)
    if not callable(fn):
        raise ValueError("active learned tool 缺少 candidate_adapter_draft(arguments) 函数。")
    output = fn(dict(arguments or {}))
    if not isinstance(output, dict):
        raise ValueError("active learned tool 必须返回 dict。")
    if str(output.get("status") or "") not in {"ok", "pass", "needs_review"}:
        raise ValueError("active learned tool 返回 status 必须为 ok/pass/needs_review。")
    return output


def _scan_candidate_adapter_ast(text: str, path: Path) -> None:
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        raise ValueError(f"active learned tool adapter 语法错误：{exc}") from exc
    allowed_import_roots = {"__future__", "typing", "json", "math", "re", "statistics", "datetime", "decimal", "fractions", "collections", "itertools", "functools", "operator"}
    blocked_call_names = {"open", "compile", "eval", "exec", "__import__", "input"}
    blocked_attr_calls = {"system", "popen", "spawn", "fork", "remove", "unlink", "rmdir", "rmtree", "copytree", "write", "write_text", "write_bytes"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = (alias.name or "").split(".")[0]
                if root not in allowed_import_roots:
                    raise ValueError(f"active learned tool adapter 导入未授权模块：{alias.name}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root not in allowed_import_roots:
                raise ValueError(f"active learned tool adapter from-import 未授权模块：{node.module}")
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in blocked_call_names:
                raise ValueError(f"active learned tool adapter 调用禁止函数：{func.id}")
            if isinstance(func, ast.Attribute) and func.attr in blocked_attr_calls:
                raise ValueError(f"active learned tool adapter 调用禁止方法：{func.attr}")



def _relative_to_workspace(path: Path, workspace: Path) -> str:
    try:
        return str(path.resolve().relative_to(workspace.resolve()).as_posix())
    except ValueError:
        return ""


def _relocatable_registry_value(path: Path, workspace: Path) -> str:
    rel = _relative_to_workspace(path, workspace)
    return rel or str(path.name)


def _relocatable_record(record: dict[str, Any], *, workspace: Path) -> dict[str, Any]:
    item = dict(record)
    for path_key, rel_key in (
        ("source_package_dir", "source_package_dir_relative"),
        ("active_dir", "active_dir_relative"),
        ("active_manifest_path", "active_manifest_relative"),
        ("source_manifest_path", "source_manifest_relative"),
        ("rollback_evidence_path", "rollback_evidence_relative"),
        ("registration_review_path", "registration_review_relative"),
    ):
        rel = _safe_text(item.get(rel_key), limit=1000)
        raw = _safe_text(item.get(path_key), limit=1200)
        if not rel and raw:
            try:
                rel = _relative_to_workspace(Path(raw), workspace)
            except (OSError, ValueError):
                rel = ""
            if rel:
                item[rel_key] = rel
        if rel:
            item[path_key] = rel
    item["path_mode"] = "workspace_relative_relocatable"
    item["relocation_supported"] = True
    return item


def _relocatable_registry_payload(payload: dict[str, Any], *, workspace: Path, active_root: Path, registry_path: Path) -> dict[str, Any]:
    item = dict(payload)
    item["workspace_root"] = "."
    item["active_root"] = _relocatable_registry_value(active_root, workspace)
    item["registry_path"] = _relocatable_registry_value(registry_path, workspace)
    item["path_mode"] = "workspace_relative_relocatable"
    item["relocation_supported"] = True
    if isinstance(item.get("records"), list):
        item["records"] = [
            _relocatable_record(record, workspace=workspace) if isinstance(record, dict) else record
            for record in item.get("records", [])
        ]
    if isinstance(item.get("activated_assets"), list):
        item["activated_assets"] = [
            _relocatable_record(record, workspace=workspace) if isinstance(record, dict) else record
            for record in item.get("activated_assets", [])
        ]
    return item


def _path_from_relative(workspace: Path, value: Any) -> Path | None:
    text = _safe_text(value, limit=500)
    if not text:
        return None
    rel = Path(text)
    if rel.is_absolute():
        return None
    candidate = (workspace / rel).resolve()
    try:
        candidate.relative_to(workspace.resolve())
    except ValueError:
        return None
    return candidate


def _manifest_identity(path: Path) -> dict[str, Any]:
    manifest_path = path / "activation_manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _record_matches_manifest(record: dict[str, Any], manifest: dict[str, Any]) -> bool:
    if not manifest:
        return False
    keys = ("tool_name", "asset_ref")
    for key in keys:
        left = _safe_text(record.get(key), limit=260)
        right = _safe_text(manifest.get(key), limit=260)
        if left and right and left == right:
            return True
    return False


def _find_active_dir(record: dict[str, Any], *, workspace: Path, active_root: Path) -> Path | None:
    candidates: list[Path] = []
    for key in ("active_dir_relative", "active_asset_relative_path"):
        candidate = _path_from_relative(workspace, record.get(key))
        if candidate is not None:
            candidates.append(candidate)
    raw_active = _safe_text(record.get("active_dir"), limit=1000)
    if raw_active:
        active_path = Path(raw_active).expanduser()
        if active_path.is_absolute():
            candidates.append(active_path)
            candidates.append(active_root / active_path.name)
        else:
            candidates.append((workspace / active_path).resolve())
    for candidate in candidates:
        if candidate.exists() and (candidate / "activation_manifest.json").exists():
            return candidate.resolve()

    for child in active_root.iterdir() if active_root.exists() else []:
        if not child.is_dir():
            continue
        manifest = _manifest_identity(child)
        if _record_matches_manifest(record, manifest):
            return child.resolve()
    return None


def _repair_record_paths(record: dict[str, Any], *, workspace: Path, active_root: Path) -> tuple[dict[str, Any], bool, bool]:
    repaired = dict(record)
    active_dir = _find_active_dir(repaired, workspace=workspace, active_root=active_root)
    if active_dir is None:
        return repaired, False, False

    before = json.dumps(repaired, sort_keys=True, ensure_ascii=False, default=str)
    repaired.update({
        "active_dir": str(active_dir),
        "active_dir_relative": _relative_to_workspace(active_dir, workspace),
        "active_manifest_path": str(active_dir / "activation_manifest.json"),
        "active_manifest_relative": _relative_to_workspace(active_dir / "activation_manifest.json", workspace),
        "rollback_evidence_path": str(active_dir / "rollback_evidence.json"),
        "rollback_evidence_relative": _relative_to_workspace(active_dir / "rollback_evidence.json", workspace),
        "registration_review_path": str(active_dir / "registration_review.json"),
        "registration_review_relative": _relative_to_workspace(active_dir / "registration_review.json", workspace),
        "path_mode": "workspace_relative_relocatable",
        "relocation_supported": True,
    })
    source_manifest = _path_from_relative(workspace, repaired.get("source_manifest_relative"))
    if source_manifest is None:
        raw_source = _safe_text(repaired.get("source_manifest_path"), limit=1000)
        if raw_source:
            raw_path = Path(raw_source)
            if raw_path.is_absolute():
                source_manifest = workspace / ".linyuanzhe" / "candidate_sandbox" / "r18" / raw_path.parent.name / raw_path.name
    source_dir = _path_from_relative(workspace, repaired.get("source_package_dir_relative"))
    if source_dir is None:
        raw_source_dir = _safe_text(repaired.get("source_package_dir"), limit=1000)
        if raw_source_dir:
            raw_dir_path = Path(raw_source_dir)
            if raw_dir_path.is_absolute():
                direct = workspace / ".linyuanzhe" / "candidate_sandbox" / "r18" / raw_dir_path.name
                nested = workspace / ".linyuanzhe" / "candidate_sandbox" / "r18" / "r21_adapter_templates" / raw_dir_path.name
                source_dir = direct if direct.exists() else nested
    if source_dir is not None and source_dir.exists():
        repaired["source_package_dir"] = str(source_dir.resolve())
        repaired["source_package_dir_relative"] = _relative_to_workspace(source_dir, workspace)
    if source_manifest is not None and source_manifest.exists():
        repaired["source_manifest_path"] = str(source_manifest.resolve())
        repaired["source_manifest_relative"] = _relative_to_workspace(source_manifest, workspace)

    changed = before != json.dumps(repaired, sort_keys=True, ensure_ascii=False, default=str)
    manifest_changed = _repair_activation_manifest(active_dir, repaired, workspace=workspace)
    return repaired, changed or manifest_changed, True


def _repair_activation_manifest(active_dir: Path, record: dict[str, Any], *, workspace: Path) -> bool:
    manifest_path = active_dir / "activation_manifest.json"
    if not manifest_path.exists():
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(manifest, dict):
        return False
    before = json.dumps(manifest, sort_keys=True, ensure_ascii=False, default=str)
    for key in (
        "active_dir",
        "active_dir_relative",
        "active_manifest_path",
        "active_manifest_relative",
        "source_package_dir",
        "source_package_dir_relative",
        "source_manifest_path",
        "source_manifest_relative",
        "rollback_evidence_path",
        "rollback_evidence_relative",
        "registration_review_path",
        "registration_review_relative",
        "path_mode",
        "relocation_supported",
    ):
        if key in record:
            manifest[key] = record[key]
    after = json.dumps(manifest, sort_keys=True, ensure_ascii=False, default=str)
    if after != before:
        _write_json(manifest_path, _relocatable_record(manifest, workspace=workspace))
        return True
    return False


def _relocate_active_records(records: list[dict[str, Any]], *, workspace: Path, active_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]], int, bool]:
    relocated_records: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []
    relocated_count = 0
    changed = False
    for record in records:
        repaired, was_changed, resolved = _repair_record_paths(record, workspace=workspace, active_root=active_root)
        relocated_records.append(repaired)
        changed = changed or was_changed
        if was_changed:
            relocated_count += 1
        if not resolved:
            issues.append(_issue(
                "active_assets.relocation",
                "P1",
                "active asset 无法按当前 workspace 重定位，learned_* 可能不可调用。",
                _safe_text(record.get("tool_name"), limit=180),
            ))
    return relocated_records, issues, relocated_count, changed


def _read_active_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema": ACTIVATION_SCHEMA, "status": "empty", "records": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"schema": ACTIVATION_SCHEMA, "status": "corrupt", "records": []}
    return payload if isinstance(payload, dict) else {"schema": ACTIVATION_SCHEMA, "status": "invalid", "records": []}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _active_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for item in _as_list(payload.get("records")):
        if not isinstance(item, dict):
            continue
        if item.get("status") == "active" and str(item.get("tool_name") or "").startswith(("learned_tool_", "learned_skill_")):
            records.append(item)
    return records


def _record_key(record: dict[str, Any]) -> str:
    return str(record.get("asset_ref") or record.get("tool_name") or record.get("source_package_ref") or "")


def _tool_name(*, kind: str, name: str, digest: str) -> str:
    prefix = "learned_tool" if kind == "tool" else "learned_skill"
    slug = re.sub(r"[^a-z0-9_]+", "_", name.lower()).strip("_")[:48] or "asset"
    return f"{prefix}_{slug}_{digest[:8]}"


def _assert_manifest_clean(manifest: dict[str, Any]) -> None:
    if not isinstance(manifest, dict):
        raise ValueError("manifest 必须是 dict。")
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
            raise ValueError(f"候选 manifest 边界字段必须为 True：{key}")


def _scan_text_files(root: Path) -> None:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() in {".zip", ".pyc"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for code, pattern in FORBIDDEN_ACTIVE_PATTERNS.items():
            if pattern.search(text):
                raise ValueError(f"active asset 静态扫描命中禁止模式：{code} at {path}")


def _issue(field: str, severity: str, message: str, ref: str = "") -> dict[str, str]:
    return {"field": field, "severity": severity, "message": message, "ref": ref}


def _no_pollution_assertions() -> dict[str, bool]:
    return {
        "copied_v1_source": False,
        "imported_v1_module": False,
        "reused_v1_registry": False,
        "reused_v1_executor": False,
        "reused_v1_provider": False,
        "reused_v1_self_iteration": False,
        "monkey_patch": False,
        "background_loop": False,
    }


def _slug_name(value: Any) -> str:
    text = _safe_text(value, limit=120).lower()
    text = re.sub(r"[^a-z0-9_\u4e00-\u9fff-]+", "_", text).strip("_")
    return text[:80] or "candidate"


def _safe_text(value: Any, *, limit: int = 700) -> str:
    text = redact_text(str(value or ""))
    text = SENSITIVE_PATTERN.sub(lambda m: f"{m.group(1)}=<redacted>", text)
    return text.strip()[:limit]


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value in (None, ""):
        return []
    return [value]
