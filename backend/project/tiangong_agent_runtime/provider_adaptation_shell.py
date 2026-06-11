"""L6.27 真实 Provider 适配外壳。

该模块把 L4 已有的五大模型 Provider factsheet / capability profile / endpoint matrix
压缩为 Runtime 外壳层可读的 ProviderProfile、ModelCapabilityMatrix、ApiSurfaceRoute、
Budget/Audit/Governance 挂载和 DryRunHealthCheckDraft。

边界：本模块只读声明，不调用任何真实模型 API，不导入 provider SDK，不读取/保存明文密钥，
不注册正式 Provider Adapter，不修改 tiangong_kernel，不允许 L6 插件裸调模型。
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

from .tool_invocation import ToolInvocation
from .tool_result import ToolResult, ToolResultStatus
from .workspace_guard import WorkspaceViolation

PROVIDER_ADAPTATION_SCHEMA = "tiangong.l6_27.provider_adaptation_shell.v1"
PROVIDER_IDS = ("deepseek_v4", "mimo", "glm_5_1", "minimax_m3", "gpt_5_5")
SENSITIVE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer|token|secret|password|credential)\s*[:=]\s*[^\s,;]+"
)
SENSITIVE_WORDS = ("api_key", "apikey", "authorization", "bearer", "token", "secret", "password")


@dataclass(frozen=True)
class ProviderProfile:
    """Provider 适配外壳的最小公开画像。"""

    provider_id: str
    display_name: str
    default_model_id: str
    supported_model_ids: list[str] = field(default_factory=list)
    protocol_family: list[str] = field(default_factory=list)
    request_api_style: str = ""
    endpoint_ref: str = ""
    credential_requirement_ref: str = "credential-handle-required"
    capability_flags: list[str] = field(default_factory=list)
    context_window_tokens: int | str = "unknown"
    max_output_tokens: int | str = "unknown"
    verified_at: str = "unknown"
    disabled_by_default: bool = True
    requires_l5_permit: bool = True
    lower_case_model_ids_required: bool = False
    unknown_or_unverified_fields: list[str] = field(default_factory=list)
    source_layer: str = "L4 model_provider_adapter factsheet"

    def __post_init__(self) -> None:
        if self.provider_id not in PROVIDER_IDS:
            raise ValueError(f"unsupported provider_id: {self.provider_id}")
        if not self.disabled_by_default or not self.requires_l5_permit:
            raise ValueError("Provider profile must remain disabled-by-default and L5-permit-gated")
        rendered = repr(self.public_dict()).lower()
        if "mockkey_" in rendered or "bearer " in rendered or "secret=" in rendered:
            raise ValueError("Provider profile cannot contain plaintext secret material")

    def public_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "display_name": self.display_name,
            "default_model_id": self.default_model_id,
            "supported_model_ids": list(self.supported_model_ids),
            "protocol_family": list(self.protocol_family),
            "request_api_style": self.request_api_style,
            "endpoint_ref": self.endpoint_ref,
            "credential_requirement_ref": self.credential_requirement_ref,
            "capability_flags": list(self.capability_flags),
            "context_window_tokens": self.context_window_tokens,
            "max_output_tokens": self.max_output_tokens,
            "verified_at": self.verified_at,
            "disabled_by_default": self.disabled_by_default,
            "requires_l5_permit": self.requires_l5_permit,
            "lower_case_model_ids_required": self.lower_case_model_ids_required,
            "unknown_or_unverified_fields": list(self.unknown_or_unverified_fields),
            "source_layer": self.source_layer,
        }


@dataclass(frozen=True)
class CapabilityMatrixRow:
    provider_id: str
    streaming: bool | str = "unknown"
    tool_calling: bool | str = "unknown"
    structured_output: bool | str = "unknown"
    json_mode: bool | str = "unknown"
    reasoning_control: bool | str = "unknown"
    thinking_mode: bool | str = "unknown"
    multimodal_input: bool | str = "unknown"
    file_input: bool | str = "unknown"
    image_input: bool | str = "unknown"
    audio_input: bool | str = "unknown"
    video_input: bool | str = "unknown"
    cache: bool | str = "unknown"
    batch: bool | str = "unknown"
    local_deployment: bool | str = "unknown"

    def public_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "streaming": self.streaming,
            "tool_calling": self.tool_calling,
            "structured_output": self.structured_output,
            "json_mode": self.json_mode,
            "reasoning_control": self.reasoning_control,
            "thinking_mode": self.thinking_mode,
            "multimodal_input": self.multimodal_input,
            "file_input": self.file_input,
            "image_input": self.image_input,
            "audio_input": self.audio_input,
            "video_input": self.video_input,
            "cache": self.cache,
            "batch": self.batch,
            "local_deployment": self.local_deployment,
        }


@dataclass(frozen=True)
class ApiSurfaceRoute:
    """普通 API / plan API / provider-native API 的声明式路由。"""

    provider_id: str
    surface_id: str
    route_kind: str
    endpoint_ref: str
    credential_scope_ref: str
    protocol_family: list[str] = field(default_factory=list)
    normal_api_supported: bool = True
    plan_api_supported: bool = False
    selected_by: str = "L3/L5/L4 envelope, not plugin code"
    live_call_enabled: bool = False
    sdk_import_required: bool = False
    notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.provider_id not in PROVIDER_IDS:
            raise ValueError(f"unsupported provider_id: {self.provider_id}")
        if self.live_call_enabled or self.sdk_import_required:
            raise ValueError("L6.27 API surface routes are declaration-only; live calls and SDK imports are forbidden")
        rendered = repr(self.public_dict()).lower()
        if "mockkey_" in rendered or "bearer " in rendered or "secret=" in rendered:
            raise ValueError("API surface route cannot contain plaintext secret material")

    def public_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "surface_id": self.surface_id,
            "route_kind": self.route_kind,
            "endpoint_ref": self.endpoint_ref,
            "credential_scope_ref": self.credential_scope_ref,
            "protocol_family": list(self.protocol_family),
            "normal_api_supported": self.normal_api_supported,
            "plan_api_supported": self.plan_api_supported,
            "selected_by": self.selected_by,
            "live_call_enabled": self.live_call_enabled,
            "sdk_import_required": self.sdk_import_required,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class GovernanceMount:
    provider_id: str
    credential_handle_required: bool = True
    credential_handle_ref: str = "credential-handle-ref:provider-runtime-scope"
    budget_permit_ref: str = "l5-budget-permit-ref:provider-runtime"
    audit_requirement_ref: str = "l5-audit-requirement-ref:provider-runtime"
    policy_permit_ref: str = "l5-policy-permit-ref:provider-runtime"
    no_plain_secret: bool = True
    no_plugin_sdk_call: bool = True
    no_l6_direct_network_call: bool = True
    l6_plugin_boundary: str = "declare capability requirement only; invoke through L3/L4 Runtime governance"
    live_call_requires_l5_permit: bool = True
    risk_level: str = "A2 declaration / A4 live credentialed request / A5 if plaintext secret or bypass attempt"

    def __post_init__(self) -> None:
        if self.provider_id not in PROVIDER_IDS:
            raise ValueError(f"unsupported provider_id: {self.provider_id}")
        required = (
            self.credential_handle_required,
            self.no_plain_secret,
            self.no_plugin_sdk_call,
            self.no_l6_direct_network_call,
            self.live_call_requires_l5_permit,
        )
        if not all(required):
            raise ValueError("Provider governance mount must keep credential/governance/network guardrails enabled")

    def public_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "credential_handle_required": self.credential_handle_required,
            "credential_handle_ref": self.credential_handle_ref,
            "budget_permit_ref": self.budget_permit_ref,
            "audit_requirement_ref": self.audit_requirement_ref,
            "policy_permit_ref": self.policy_permit_ref,
            "no_plain_secret": self.no_plain_secret,
            "no_plugin_sdk_call": self.no_plugin_sdk_call,
            "no_l6_direct_network_call": self.no_l6_direct_network_call,
            "l6_plugin_boundary": self.l6_plugin_boundary,
            "live_call_requires_l5_permit": self.live_call_requires_l5_permit,
            "risk_level": self.risk_level,
        }


@dataclass(frozen=True)
class ProviderHealthCheckDraft:
    """干跑健康检查草案，不触网。"""

    provider_id: str
    status: str
    checks: list[str] = field(default_factory=list)
    dry_run_only: bool = True
    performs_network_call: bool = False
    reads_credentials: bool = False
    recommended_next_check: str = "when L5 permit and credential handle exist, run provider-specific dry-run mapper smoke, still no plugin direct call"

    def __post_init__(self) -> None:
        if self.provider_id not in PROVIDER_IDS:
            raise ValueError(f"unsupported provider_id: {self.provider_id}")
        if not self.dry_run_only or self.performs_network_call or self.reads_credentials:
            raise ValueError("Provider health check draft must stay dry-run only and cannot read credentials or call network")

    def public_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "status": self.status,
            "checks": list(self.checks),
            "dry_run_only": self.dry_run_only,
            "performs_network_call": self.performs_network_call,
            "reads_credentials": self.reads_credentials,
            "recommended_next_check": self.recommended_next_check,
        }


@dataclass(frozen=True)
class ProviderAdaptationReport:
    schema: str
    generated_at: float
    status: str
    summary: str
    baseline: str = "L6.26-delivery-standardization-shell"
    provider_profiles: list[ProviderProfile] = field(default_factory=list)
    capability_matrix: list[CapabilityMatrixRow] = field(default_factory=list)
    api_surface_routes: list[ApiSurfaceRoute] = field(default_factory=list)
    governance_mounts: list[GovernanceMount] = field(default_factory=list)
    health_check_drafts: list[ProviderHealthCheckDraft] = field(default_factory=list)
    provider_count: int = 0
    route_count: int = 0
    shell_mount_status: str = "unknown"
    delivery_standard_status: str = "unknown"
    audit_summary: list[dict[str, Any]] = field(default_factory=list)
    report_digest: str = ""
    execution_first: bool = True
    shell_only: bool = True
    provider_declaration_only: bool = True
    kernel_pollution_guard: bool = True
    performs_network_call: bool = False
    reads_credentials: bool = False
    stores_credentials: bool = False
    imports_provider_sdk: bool = False
    invokes_model: bool = False
    registers_formal_provider_adapter: bool = False
    modifies_kernel: bool = False
    modifies_core_runtime: bool = False
    bypasses_governance: bool = False

    def __post_init__(self) -> None:
        if not (self.execution_first and self.shell_only and self.provider_declaration_only and self.kernel_pollution_guard):
            raise ValueError("L6.27 Provider adaptation must remain execution-first, shell-only, declaration-only and kernel-guarded")
        forbidden = (
            self.performs_network_call,
            self.reads_credentials,
            self.stores_credentials,
            self.imports_provider_sdk,
            self.invokes_model,
            self.registers_formal_provider_adapter,
            self.modifies_kernel,
            self.modifies_core_runtime,
            self.bypasses_governance,
        )
        if any(forbidden):
            raise ValueError("L6.27 Provider adaptation cannot call network/read credentials/import SDK/invoke/register/mutate/bypass")
        if self.provider_count and self.provider_count != len(self.provider_profiles):
            raise ValueError("provider_count mismatch")
        if self.route_count and self.route_count != len(self.api_surface_routes):
            raise ValueError("route_count mismatch")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "status": self.status,
            "summary": self.summary,
            "baseline": self.baseline,
            "provider_profiles": [item.public_dict() for item in self.provider_profiles],
            "capability_matrix": [item.public_dict() for item in self.capability_matrix],
            "api_surface_routes": [item.public_dict() for item in self.api_surface_routes],
            "governance_mounts": [item.public_dict() for item in self.governance_mounts],
            "health_check_drafts": [item.public_dict() for item in self.health_check_drafts],
            "provider_count": self.provider_count,
            "route_count": self.route_count,
            "shell_mount_status": self.shell_mount_status,
            "delivery_standard_status": self.delivery_standard_status,
            "audit_summary": list(self.audit_summary),
            "report_digest": self.report_digest,
            "execution_first": self.execution_first,
            "shell_only": self.shell_only,
            "provider_declaration_only": self.provider_declaration_only,
            "kernel_pollution_guard": self.kernel_pollution_guard,
            "performs_network_call": self.performs_network_call,
            "reads_credentials": self.reads_credentials,
            "stores_credentials": self.stores_credentials,
            "imports_provider_sdk": self.imports_provider_sdk,
            "invokes_model": self.invokes_model,
            "registers_formal_provider_adapter": self.registers_formal_provider_adapter,
            "modifies_kernel": self.modifies_kernel,
            "modifies_core_runtime": self.modifies_core_runtime,
            "bypasses_governance": self.bypasses_governance,
        }

    def summary_text(self) -> str:
        return (
            "L6.27 Provider 适配外壳："
            f"status={self.status}；providers={self.provider_count}；routes={self.route_count}；"
            f"shell_only={self.shell_only}；declaration_only={self.provider_declaration_only}；"
            f"kernel_pollution_guard={self.kernel_pollution_guard}。{self.summary}"
        )

    def markdown_report(self) -> str:
        lines = [
            "# 临渊者 L6.27 Provider 适配外壳报告",
            "",
            f"- schema: `{self.schema}`",
            f"- status: `{self.status}`",
            f"- baseline: `{self.baseline}`",
            f"- provider_count: `{self.provider_count}`",
            f"- route_count: `{self.route_count}`",
            f"- shell_only: `{self.shell_only}`",
            f"- provider_declaration_only: `{self.provider_declaration_only}`",
            f"- kernel_pollution_guard: `{self.kernel_pollution_guard}`",
            "",
            "## 摘要",
            "",
            self.summary,
            "",
            "## Provider Profiles",
        ]
        for profile in self.provider_profiles:
            lines.append(
                f"- `{profile.provider_id}`：{profile.display_name}；default={profile.default_model_id}；"
                f"protocol={','.join(profile.protocol_family)}；credential={profile.credential_requirement_ref}；"
                f"unknown={len(profile.unknown_or_unverified_fields)}"
            )
        lines += ["", "## API Surface Routes"]
        for route in self.api_surface_routes:
            lines.append(
                f"- `{route.provider_id}/{route.surface_id}`：kind={route.route_kind}；"
                f"normal={route.normal_api_supported}；plan={route.plan_api_supported}；live_call={route.live_call_enabled}"
            )
        lines += ["", "## Governance Mounts"]
        for mount in self.governance_mounts:
            lines.append(
                f"- `{mount.provider_id}`：credential_handle_required={mount.credential_handle_required}；"
                f"no_plugin_sdk_call={mount.no_plugin_sdk_call}；risk={mount.risk_level}"
            )
        lines += ["", "## Health Check Drafts"]
        for draft in self.health_check_drafts:
            lines.append(f"- `{draft.provider_id}`：{draft.status}；checks={len(draft.checks)}；dry_run_only={draft.dry_run_only}")
        lines += ["", "## 强边界", ""]
        lines.append("- 不调用真实模型 API。")
        lines.append("- 不读取、不保存、不显示明文凭证。")
        lines.append("- 不导入 provider SDK。")
        lines.append("- 不注册正式 Provider Adapter。")
        lines.append("- L6 插件不得裸调模型，必须经 L3/L4/L5 治理链。")
        return "\n".join(lines)


class ProviderAdaptationBridge:
    """L6.27 Provider 适配外壳状态桥。"""

    def __init__(self) -> None:
        self._last_report: ProviderAdaptationReport | None = None

    @property
    def last_report(self) -> ProviderAdaptationReport | None:
        return self._last_report

    def reset(self) -> None:
        self._last_report = None

    def build(
        self,
        *,
        shell_mount: dict[str, Any] | None = None,
        delivery_standardization: dict[str, Any] | None = None,
        audit_summary: Iterable[dict[str, Any]] | None = None,
        notes: str = "",
    ) -> ProviderAdaptationReport:
        profiles, matrix, routes, governance, health = _build_provider_payload()
        shell_status = str((shell_mount or {}).get("status") or "unknown")
        delivery_status = str((delivery_standardization or {}).get("status") or "unknown")
        safe_notes = _sanitize_text(notes)[:800]
        summary = (
            "已从 L4 provider factsheet / capability profile 读取五大模型声明，生成普通 API 与 plan API 的声明式路由、"
            "预算/审计/策略/凭证句柄挂载和干跑健康检查草案。该报告不触网、不读密钥、不注册正式适配器，"
            "只为后续 L3/L4/L5 真实 Provider 执行链提供外壳地图。"
        )
        if safe_notes:
            summary += f" 备注：{safe_notes}"
        report = ProviderAdaptationReport(
            schema=PROVIDER_ADAPTATION_SCHEMA,
            generated_at=time(),
            status="provider_adaptation_shell_ready",
            summary=summary,
            provider_profiles=profiles,
            capability_matrix=matrix,
            api_surface_routes=routes,
            governance_mounts=governance,
            health_check_drafts=health,
            provider_count=len(profiles),
            route_count=len(routes),
            shell_mount_status=shell_status,
            delivery_standard_status=delivery_status,
            audit_summary=_sanitize_audit(list(audit_summary or [])[-30:]),
        )
        digest = stable_provider_adaptation_digest(report)
        report = ProviderAdaptationReport(
            schema=report.schema,
            generated_at=report.generated_at,
            status=report.status,
            summary=report.summary,
            baseline=report.baseline,
            provider_profiles=report.provider_profiles,
            capability_matrix=report.capability_matrix,
            api_surface_routes=report.api_surface_routes,
            governance_mounts=report.governance_mounts,
            health_check_drafts=report.health_check_drafts,
            provider_count=report.provider_count,
            route_count=report.route_count,
            shell_mount_status=report.shell_mount_status,
            delivery_standard_status=report.delivery_standard_status,
            audit_summary=report.audit_summary,
            report_digest=digest,
        )
        self._last_report = report
        return report

    def public_dict(self) -> dict[str, Any]:
        if self._last_report is None:
            return {
                "schema": PROVIDER_ADAPTATION_SCHEMA,
                "status": "empty",
                "message": "暂无 L6.27 Provider 适配外壳报告，请先执行 /provider-build。",
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
        digest = str(payload.get("report_digest") or "")
        providers = [p.get("provider_id") for p in payload.get("provider_profiles", [])]
        return (
            "L6.27 Provider 适配外壳已生成："
            f"status={payload.get('status')}；providers={providers}；routes={payload.get('route_count')}；"
            f"declaration_only={payload.get('provider_declaration_only')}；digest={digest[:12]}。"
        )


def build_provider_adaptation_adapter(
    bridge: ProviderAdaptationBridge,
    shell_mount_bridge: Any,
    delivery_standardization_bridge: Any,
    audit_bridge: Any,
):
    def provider_adaptation_adapter(invocation: ToolInvocation, context: Any) -> ToolResult:
        try:
            report = bridge.build(
                shell_mount=shell_mount_bridge.public_dict(),
                delivery_standardization=delivery_standardization_bridge.public_dict(),
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
                output_summary=f"L6.27 Provider 适配外壳被阻断：{exc}",
                error_code="provider_adaptation_blocked",
            )
        except OSError as exc:
            return ToolResult(
                step_id=invocation.step_id,
                tool_name=invocation.tool_name,
                status=ToolResultStatus.FAILED,
                output_summary=f"L6.27 Provider 适配外壳失败：{exc}",
                error_code="provider_adaptation_failed",
            )

    return provider_adaptation_adapter


def stable_provider_adaptation_digest(report: ProviderAdaptationReport) -> str:
    payload = report.public_dict()
    payload.pop("generated_at", None)
    payload["report_digest"] = ""
    return _stable_digest(payload)


def _build_provider_payload() -> tuple[list[ProviderProfile], list[CapabilityMatrixRow], list[ApiSurfaceRoute], list[GovernanceMount], list[ProviderHealthCheckDraft]]:
    factsheets = _load_l4_factsheets()
    profiles: list[ProviderProfile] = []
    matrix: list[CapabilityMatrixRow] = []
    routes: list[ApiSurfaceRoute] = []
    governance: list[GovernanceMount] = []
    health: list[ProviderHealthCheckDraft] = []
    for provider_id in PROVIDER_IDS:
        fs = factsheets[provider_id]
        profile = ProviderProfile(
            provider_id=provider_id,
            display_name=str(fs.get("provider_display_name") or provider_id),
            default_model_id=str(fs.get("default_model_id") or "unknown"),
            supported_model_ids=[str(item) for item in fs.get("supported_model_ids", [])],
            protocol_family=[str(item) for item in fs.get("protocol_family", [])],
            request_api_style=str(fs.get("request_api_style") or "unknown"),
            endpoint_ref=str(fs.get("base_url_ref") or "official-ref:unknown"),
            credential_requirement_ref=str(fs.get("auth_scheme_ref") or "credential-handle-required"),
            capability_flags=_capability_flags_from_factsheet(fs),
            context_window_tokens=fs.get("context_window_tokens", "unknown"),
            max_output_tokens=fs.get("max_output_tokens", "unknown"),
            verified_at=str(fs.get("verified_at") or "unknown"),
            lower_case_model_ids_required=provider_id == "mimo",
            unknown_or_unverified_fields=[str(item) for item in fs.get("unknown_or_unverified_fields", [])],
        )
        profiles.append(profile)
        matrix.append(_matrix_row(provider_id, fs))
        routes.extend(_routes_for(provider_id, fs))
        governance.append(
            GovernanceMount(
                provider_id=provider_id,
                credential_handle_ref=f"credential-handle-ref:{provider_id}",
                budget_permit_ref=f"l5-budget-permit-ref:{provider_id}",
                audit_requirement_ref=f"l5-audit-requirement-ref:{provider_id}",
                policy_permit_ref=f"l5-policy-permit-ref:{provider_id}",
            )
        )
        health.append(
            ProviderHealthCheckDraft(
                provider_id=provider_id,
                status="dry_run_health_check_declared",
                checks=[
                    "factsheet_loaded_from_l4",
                    "credential_handle_ref_only",
                    "budget_permit_ref_declared",
                    "audit_requirement_ref_declared",
                    "policy_permit_ref_declared",
                    "no_plugin_sdk_call",
                    "no_l6_direct_network_call",
                    "api_surface_route_declared",
                ],
            )
        )
    return profiles, matrix, routes, governance, health


def _load_l4_factsheets() -> dict[str, dict[str, Any]]:
    # 只读 L4 声明；不修改 tiangong_kernel，不实例化任何真实网络 client。
    from tiangong_kernel.l4_action_grounding.model_provider_adapter import all_provider_factsheets

    raw = all_provider_factsheets()
    result: dict[str, dict[str, Any]] = {}
    for provider_id in PROVIDER_IDS:
        factsheet = raw[provider_id]
        if hasattr(factsheet, "to_dict"):
            result[provider_id] = factsheet.to_dict()
        else:
            result[provider_id] = dict(factsheet)
    return result


def _capability_flags_from_factsheet(fs: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    fields = (
        "streaming_supported",
        "tool_calling_supported",
        "structured_output_supported",
        "json_mode_supported",
        "reasoning_control_supported",
        "thinking_mode_supported",
        "multimodal_input_supported",
        "file_input_supported",
        "image_input_supported",
        "audio_input_supported",
        "video_input_supported",
        "cache_supported",
        "batch_supported",
    )
    for name in fields:
        value = fs.get(name)
        label = name.replace("_supported", "")
        if value is True:
            flags.append(label)
        elif value == "unknown":
            flags.append(f"{label}:unknown")
    if fs.get("local_deployment_supported") is True:
        flags.append("local_deployment")
    elif fs.get("local_deployment_supported") == "unknown":
        flags.append("local_deployment:unknown")
    return flags


def _matrix_row(provider_id: str, fs: dict[str, Any]) -> CapabilityMatrixRow:
    return CapabilityMatrixRow(
        provider_id=provider_id,
        streaming=fs.get("streaming_supported", "unknown"),
        tool_calling=fs.get("tool_calling_supported", "unknown"),
        structured_output=fs.get("structured_output_supported", "unknown"),
        json_mode=fs.get("json_mode_supported", "unknown"),
        reasoning_control=fs.get("reasoning_control_supported", "unknown"),
        thinking_mode=fs.get("thinking_mode_supported", "unknown"),
        multimodal_input=fs.get("multimodal_input_supported", "unknown"),
        file_input=fs.get("file_input_supported", "unknown"),
        image_input=fs.get("image_input_supported", "unknown"),
        audio_input=fs.get("audio_input_supported", "unknown"),
        video_input=fs.get("video_input_supported", "unknown"),
        cache=fs.get("cache_supported", "unknown"),
        batch=fs.get("batch_supported", "unknown"),
        local_deployment=fs.get("local_deployment_supported", "unknown"),
    )


def _routes_for(provider_id: str, fs: dict[str, Any]) -> list[ApiSurfaceRoute]:
    protocols = [str(item) for item in fs.get("protocol_family", [])]
    endpoint_ref = str(fs.get("base_url_ref") or f"official-ref:{provider_id}")
    routes: list[ApiSurfaceRoute] = []
    if provider_id == "mimo":
        routes.append(
            ApiSurfaceRoute(
                provider_id=provider_id,
                surface_id="ordinary_api",
                route_kind="normal_api",
                endpoint_ref="provider-endpoint-ref:mimo:ordinary_api",
                credential_scope_ref="credential-scope-ref:mimo:ordinary_api",
                protocol_family=protocols,
                normal_api_supported=True,
                plan_api_supported=False,
                notes=["MiMo model ids must remain lowercase", "ordinary API and token plan credentials cannot be mixed"],
            )
        )
        routes.append(
            ApiSurfaceRoute(
                provider_id=provider_id,
                surface_id="token_plan_api",
                route_kind="plan_api",
                endpoint_ref="provider-endpoint-ref:mimo:token_plan_api",
                credential_scope_ref="credential-scope-ref:mimo:token_plan_api",
                protocol_family=protocols,
                normal_api_supported=False,
                plan_api_supported=True,
                notes=["token plan API is selected by credential/provider scope", "MiMo model ids must remain lowercase"],
            )
        )
        return routes
    if provider_id == "gpt_5_5":
        routes.append(
            ApiSurfaceRoute(
                provider_id=provider_id,
                surface_id="responses_api",
                route_kind="normal_api_with_reasoning_controls",
                endpoint_ref=endpoint_ref,
                credential_scope_ref="credential-scope-ref:gpt_5_5:responses_api",
                protocol_family=protocols,
                normal_api_supported=True,
                plan_api_supported=True,
                notes=["reasoning controls are declared through envelope parameters", "no direct OpenAI SDK import in L6 shell"],
            )
        )
        return routes
    route_kind = "normal_api_with_plan_parameters" if fs.get("reasoning_control_supported") is True else "normal_api"
    routes.append(
        ApiSurfaceRoute(
            provider_id=provider_id,
            surface_id="primary_api",
            route_kind=route_kind,
            endpoint_ref=endpoint_ref,
            credential_scope_ref=f"credential-scope-ref:{provider_id}:primary_api",
            protocol_family=protocols,
            normal_api_supported=True,
            plan_api_supported=fs.get("reasoning_control_supported") is True,
            notes=["provider adapter remains disabled until L5 permit exists", "request/response normalization belongs to L4 mapper"],
        )
    )
    return routes


def _sanitize_text(text: str) -> str:
    cleaned = redact_text(str(text or ""))
    cleaned = SENSITIVE_PATTERN.sub(lambda m: m.group(1) + "=<redacted>", cleaned)
    return cleaned.replace("\x00", "")


def _sanitize_audit(events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    sanitized: list[dict[str, Any]] = []
    for event in events:
        if isinstance(event, dict):
            sanitized.append(_sanitize_mapping(event))
    return sanitized


def _sanitize_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    item: dict[str, Any] = {}
    for key, value in mapping.items():
        key_text = str(key)
        if any(word in key_text.lower() for word in SENSITIVE_WORDS):
            item[key_text] = "<redacted>"
        else:
            item[key_text] = _sanitize_value(value)
    return item


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return _sanitize_text(value)[:500]
    if isinstance(value, dict):
        return _sanitize_mapping(value)
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value[:50]]
    if isinstance(value, tuple):
        return tuple(_sanitize_value(item) for item in value[:50])
    return value


def _stable_digest(payload: dict[str, Any]) -> str:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()
