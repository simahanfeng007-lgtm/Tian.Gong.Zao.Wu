"""L5 插件模型能力治理兼容补丁。

本模块只提供新增不变量、许可对象和静态扫描辅助，不调用模型 API，不导入 provider SDK，不发送 HTTP 请求。
L5 的职责是治理和签发 permit；真实 provider adapter 承载于 L4。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any, Mapping

L5_MODEL_CAPABILITY_SCHEMA_VERSION = "0.1.hotfix3-p2p3-final-five-model"
RAW_MODEL_SDK_IMPORT_PATTERNS = (
    r"^\s*import\s+openai\b",
    r"^\s*from\s+openai\b",
    r"^\s*import\s+anthropic\b",
    r"^\s*from\s+anthropic\b",
    r"^\s*import\s+google\.genai\b",
    r"^\s*from\s+google\.genai\b",
    r"^\s*import\s+dashscope\b",
    r"^\s*from\s+dashscope\b",
    r"^\s*import\s+zhipuai\b",
    r"^\s*from\s+zhipuai\b",
    r"^\s*import\s+minimax\b",
    r"^\s*from\s+minimax\b",
    r"^\s*import\s+deepseek\b",
    r"^\s*from\s+deepseek\b",
)
RAW_MODEL_HTTP_PATTERNS = (
    r"api\.openai\.com",
    r"api\.deepseek\.com",
    r"api\.z\.ai",
    r"bigmodel\.cn",
    r"api\.minimax",
    r"api\.minimaxi",
    r"platform\.xiaomimimo",
    r"token-plan-cn\.xiaomimimo",
    r"base_url\s*=\s*['\"]https?://",
    r"api[_-]?key\s*=\s*['\"]",
    r"os\.environ\[[\'\"][A-Z0-9_]*(OPENAI|DEEPSEEK|ZHIPU|MINIMAX|MIMO)[A-Z0-9_]*[\'\"]\]",
)


def _ensure_ref(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > 256:
        raise ValueError(f"{field_name} must be a non-empty short reference")
    lowered = value.lower()
    if "sk-" in lowered or "bearer " in lowered or "secret=" in lowered:
        raise ValueError(f"{field_name} cannot contain plaintext secret material")


@dataclass(frozen=True, slots=True)
class ModelProviderPermitScope:
    allowed_provider_ids: tuple[str, ...]
    allowed_model_ids: tuple[str, ...] = field(default_factory=tuple)
    tool_call_allowed: bool = False
    streaming_allowed: bool = False
    structured_output_allowed: bool = False
    multimodal_allowed: bool = False
    schema_version: str = L5_MODEL_CAPABILITY_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ModelInvocationBudgetPermitRef:
    budget_permit_ref: str
    schema_version: str = L5_MODEL_CAPABILITY_SCHEMA_VERSION
    def __post_init__(self) -> None: _ensure_ref(self.budget_permit_ref, "budget_permit_ref")


@dataclass(frozen=True, slots=True)
class ModelInvocationAuditRequirementRef:
    audit_requirement_ref: str
    schema_version: str = L5_MODEL_CAPABILITY_SCHEMA_VERSION
    def __post_init__(self) -> None: _ensure_ref(self.audit_requirement_ref, "audit_requirement_ref")


@dataclass(frozen=True, slots=True)
class ModelInvocationCredentialHandleRef:
    credential_handle_ref: str
    schema_version: str = L5_MODEL_CAPABILITY_SCHEMA_VERSION
    def __post_init__(self) -> None: _ensure_ref(self.credential_handle_ref, "credential_handle_ref")


@dataclass(frozen=True, slots=True)
class ModelInvocationPermit:
    permit_ref: str
    provider_scope: ModelProviderPermitScope
    budget_permit_ref: ModelInvocationBudgetPermitRef
    audit_requirement_ref: ModelInvocationAuditRequirementRef
    credential_handle_ref: ModelInvocationCredentialHandleRef
    policy_permit_ref: str
    context_policy_ref: str
    expires_at_ref: str | None = None
    permit_only: bool = True
    not_a_model_client: bool = True
    schema_version: str = L5_MODEL_CAPABILITY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.permit_ref, "permit_ref")
        _ensure_ref(self.policy_permit_ref, "policy_permit_ref")
        _ensure_ref(self.context_policy_ref, "context_policy_ref")
        if not self.permit_only or not self.not_a_model_client:
            raise ValueError("L5 can only issue model invocation permit, not model client")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PluginModelAccessPolicy:
    plugin_id: str
    capability_requirement_ref: str
    model_access_must_use_l3_l5_l4_chain: bool = True
    raw_provider_call_forbidden: bool = True
    schema_version: str = L5_MODEL_CAPABILITY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.plugin_id, "plugin_id")
        _ensure_ref(self.capability_requirement_ref, "capability_requirement_ref")
        if not self.model_access_must_use_l3_l5_l4_chain or not self.raw_provider_call_forbidden:
            raise ValueError("plugins must use L3/L5/L4 model governance chain")


@dataclass(frozen=True, slots=True)
class ModelCredentialHandleOnlyPolicy:
    credential_handle_required: bool = True
    plaintext_secret_forbidden: bool = True
    schema_version: str = L5_MODEL_CAPABILITY_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ModelBudgetRequiredPolicy:
    budget_required: bool = True
    schema_version: str = L5_MODEL_CAPABILITY_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ModelAuditRequiredPolicy:
    audit_required: bool = True
    schema_version: str = L5_MODEL_CAPABILITY_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ModelContextPolicyRequired:
    context_policy_required: bool = True
    schema_version: str = L5_MODEL_CAPABILITY_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ModelProviderAllowlistPolicy:
    allowed_provider_ids: tuple[str, ...]
    schema_version: str = L5_MODEL_CAPABILITY_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ModelProviderScopePolicy:
    provider_scope: ModelProviderPermitScope
    schema_version: str = L5_MODEL_CAPABILITY_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class PluginModelCapabilityRequirementOnlyInvariant:
    plugin_id: str
    declared_requirement_refs: tuple[str, ...]
    no_model_client: bool = True
    no_direct_dispatch: bool = True
    schema_version: str = L5_MODEL_CAPABILITY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_ref(self.plugin_id, "plugin_id")
        if not self.no_model_client or not self.no_direct_dispatch:
            raise ValueError("plugins may only declare ModelCapabilityRequirement")


@dataclass(frozen=True, slots=True)
class NoPluginRawModelSDKInvariant:
    plugin_id: str
    scan_violations: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L5_MODEL_CAPABILITY_SCHEMA_VERSION

    @property
    def passed(self) -> bool:
        return len(self.scan_violations) == 0


@dataclass(frozen=True, slots=True)
class NoPluginRawHTTPModelCallInvariant:
    plugin_id: str
    scan_violations: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L5_MODEL_CAPABILITY_SCHEMA_VERSION

    @property
    def passed(self) -> bool:
        return len(self.scan_violations) == 0


def scan_plugin_source_for_raw_model_access(source: str) -> tuple[str, ...]:
    violations: list[str] = []
    for pattern in RAW_MODEL_SDK_IMPORT_PATTERNS:
        if re.search(pattern, source, flags=re.MULTILINE):
            violations.append(f"raw_model_sdk_import:{pattern}")
    for pattern in RAW_MODEL_HTTP_PATTERNS:
        if re.search(pattern, source, flags=re.IGNORECASE | re.MULTILINE):
            violations.append(f"raw_model_http_or_secret:{pattern}")
    return tuple(violations)


def build_plugin_model_access_invariants(plugin_id: str, source: str, requirement_refs: tuple[str, ...]) -> tuple[PluginModelCapabilityRequirementOnlyInvariant, NoPluginRawModelSDKInvariant, NoPluginRawHTTPModelCallInvariant]:
    _ensure_ref(plugin_id, "plugin_id")
    violations = scan_plugin_source_for_raw_model_access(source)
    sdk = tuple(v for v in violations if v.startswith("raw_model_sdk_import"))
    http = tuple(v for v in violations if v.startswith("raw_model_http_or_secret"))
    return (
        PluginModelCapabilityRequirementOnlyInvariant(plugin_id=plugin_id, declared_requirement_refs=requirement_refs),
        NoPluginRawModelSDKInvariant(plugin_id=plugin_id, scan_violations=sdk),
        NoPluginRawHTTPModelCallInvariant(plugin_id=plugin_id, scan_violations=http),
    )
