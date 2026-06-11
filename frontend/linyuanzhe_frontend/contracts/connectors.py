from __future__ import annotations

"""L6.66 MCP / connector registry frontend governance contract.

The desktop frontend may display sanitized connector registry projections and
submit connector registration/quarantine request envelopes to Runtime. It may
not install MCP servers, execute connector tools, store connector secrets,
bypass Agent Workspace authorization, write audit/memory, or apply rollback.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping
import hashlib

CONNECTOR_REGISTRY_CONTRACT_VERSION = "tiangong.l6_66.connector_registry.v1"
CONNECTOR_REGISTRY_ENDPOINT = "/connectors/registry"
CONNECTOR_REGISTER_ENDPOINT = "/connectors/register/request"
CONNECTOR_QUARANTINE_ENDPOINT = "/connectors/quarantine/request"

ALLOWED_CONNECTOR_KINDS = (
    "mcp_server",
    "local_connector",
    "remote_connector",
    "document_connector",
    "browser_connector",
    "workflow_connector",
)
ALLOWED_CONNECTOR_MODES = ("disabled", "read_only", "request_only", "quarantined")
ALLOWED_CONNECTOR_TRUST_LEVELS = ("builtin", "signed", "workspace_local", "external_review_required", "unknown")
ALLOWED_CONNECTOR_SCOPES = (
    "read_public_metadata",
    "read_user_selected_files",
    "workspace_read",
    "workspace_write_request",
    "browser_readonly",
    "network_request_via_runtime",
    "tool_request_via_runtime",
)
MAX_CONNECTOR_RECORDS = 40


def safe_text(value: Any, max_len: int = 260) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\r", " ").replace("\n", " ").strip()
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text


def digest_text(value: Any, length: int = 16) -> str:
    data = ("" if value is None else str(value)).encode("utf-8", errors="ignore")
    return hashlib.sha256(data).hexdigest()[:length]


def _safe_list(values: Any, allowed: tuple[str, ...], *, default: str = "read_public_metadata") -> List[str]:
    if not isinstance(values, (list, tuple, set)):
        values = [values] if values else []
    out: List[str] = []
    for raw in values:
        item = safe_text(raw, 80)
        if item in allowed and item not in out:
            out.append(item)
    return out or [default]


@dataclass(frozen=True)
class ConnectorManifestProjection:
    connector_id_digest: str = ""
    display_name: str = "未注册连接器"
    kind: str = "mcp_server"
    version: str = "0.0.0"
    trust_level: str = "unknown"
    default_mode: str = "disabled"
    requested_scopes: List[str] = field(default_factory=lambda: ["read_public_metadata"])
    capabilities: List[str] = field(default_factory=list)
    manifest_digest: str = ""
    signature_digest: str = ""
    source_digest: str = ""
    risk_level: str = "A3"
    status: str = "unregistered"
    read_only_default: bool = True
    quality_gate_required: bool = True
    workspace_authorization_required: bool = True
    runtime_authority_required: bool = True
    quarantined: bool = False
    raw_endpoint_visible: bool = False
    raw_secret_visible: bool = False
    frontend_may_install: bool = False
    frontend_may_execute: bool = False
    frontend_may_store_secret: bool = False

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ConnectorManifestProjection":
        payload = data.get("payload", data) if isinstance(data, Mapping) else {}
        if not isinstance(payload, Mapping):
            payload = {}
        kind = safe_text(payload.get("kind", "mcp_server"), 80)
        if kind not in ALLOWED_CONNECTOR_KINDS:
            kind = "mcp_server"
        mode = safe_text(payload.get("default_mode", "disabled"), 40)
        if mode not in ALLOWED_CONNECTOR_MODES:
            mode = "disabled"
        trust = safe_text(payload.get("trust_level", "unknown"), 80)
        if trust not in ALLOWED_CONNECTOR_TRUST_LEVELS:
            trust = "unknown"
        raw_id = payload.get("connector_id", payload.get("id", payload.get("display_name", "")))
        return cls(
            connector_id_digest=safe_text(payload.get("connector_id_digest", digest_text(raw_id)), 32),
            display_name=safe_text(payload.get("display_name", payload.get("name", "未注册连接器")), 120),
            kind=kind,
            version=safe_text(payload.get("version", "0.0.0"), 60),
            trust_level=trust,
            default_mode=mode,
            requested_scopes=_safe_list(payload.get("requested_scopes", payload.get("scopes", [])), ALLOWED_CONNECTOR_SCOPES),
            capabilities=[safe_text(x, 80) for x in (payload.get("capabilities", []) or [])[:12]],
            manifest_digest=safe_text(payload.get("manifest_digest", digest_text(payload)), 32),
            signature_digest=safe_text(payload.get("signature_digest", ""), 32),
            source_digest=safe_text(payload.get("source_digest", ""), 32),
            risk_level=safe_text(payload.get("risk_level", "A3"), 16),
            status=safe_text(payload.get("status", "unregistered"), 80),
            read_only_default=bool(payload.get("read_only_default", True)),
            quality_gate_required=bool(payload.get("quality_gate_required", True)),
            workspace_authorization_required=bool(payload.get("workspace_authorization_required", True)),
            runtime_authority_required=bool(payload.get("runtime_authority_required", True)),
            quarantined=bool(payload.get("quarantined", False)),
            raw_endpoint_visible=bool(payload.get("raw_endpoint_visible", False)),
            raw_secret_visible=bool(payload.get("raw_secret_visible", False)),
            frontend_may_install=bool(payload.get("frontend_may_install", False)),
            frontend_may_execute=bool(payload.get("frontend_may_execute", False)),
            frontend_may_store_secret=bool(payload.get("frontend_may_store_secret", False)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConnectorRegistryProjection:
    registry_id_digest: str = ""
    registry_state: str = "ready"
    default_mode: str = "disabled"
    connector_count: int = 0
    enabled_count: int = 0
    read_only_count: int = 0
    quarantined_count: int = 0
    pending_review_count: int = 0
    allow_market_install: bool = False
    allow_unsigned_connector: bool = False
    runtime_authority_required: bool = True
    quality_gate_required: bool = True
    workspace_authorization_required: bool = True
    frontend_may_install_connector: bool = False
    frontend_may_execute_connector: bool = False
    frontend_may_store_connector_secret: bool = False
    endpoints: Dict[str, str] = field(default_factory=lambda: {
        "registry": CONNECTOR_REGISTRY_ENDPOINT,
        "register_request": CONNECTOR_REGISTER_ENDPOINT,
        "quarantine_request": CONNECTOR_QUARANTINE_ENDPOINT,
    })

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ConnectorRegistryProjection":
        payload = data.get("payload", data) if isinstance(data, Mapping) else {}
        if not isinstance(payload, Mapping):
            payload = {}
        return cls(
            registry_id_digest=safe_text(payload.get("registry_id_digest", digest_text(payload.get("registry_id", ""))), 32),
            registry_state=safe_text(payload.get("registry_state", payload.get("state", "ready")), 80),
            default_mode=safe_text(payload.get("default_mode", "disabled"), 40),
            connector_count=int(payload.get("connector_count", 0) or 0),
            enabled_count=int(payload.get("enabled_count", 0) or 0),
            read_only_count=int(payload.get("read_only_count", 0) or 0),
            quarantined_count=int(payload.get("quarantined_count", 0) or 0),
            pending_review_count=int(payload.get("pending_review_count", 0) or 0),
            allow_market_install=bool(payload.get("allow_market_install", False)),
            allow_unsigned_connector=bool(payload.get("allow_unsigned_connector", False)),
            runtime_authority_required=bool(payload.get("runtime_authority_required", True)),
            quality_gate_required=bool(payload.get("quality_gate_required", True)),
            workspace_authorization_required=bool(payload.get("workspace_authorization_required", True)),
            frontend_may_install_connector=bool(payload.get("frontend_may_install_connector", False)),
            frontend_may_execute_connector=bool(payload.get("frontend_may_execute_connector", False)),
            frontend_may_store_connector_secret=bool(payload.get("frontend_may_store_connector_secret", False)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConnectorRegistrationRequest:
    display_name: str = ""
    kind: str = "mcp_server"
    version: str = "0.0.0"
    requested_scopes: List[str] = field(default_factory=lambda: ["read_public_metadata"])
    requested_capabilities: List[str] = field(default_factory=list)
    manifest_digest: str = ""
    source_digest: str = ""
    signature_digest: str = ""
    trust_level: str = "unknown"
    default_mode: str = "disabled"
    purpose: str = "connector_registry_review"
    run_id: str = ""
    task_id: str = ""
    frontend_contract: str = CONNECTOR_REGISTRY_CONTRACT_VERSION
    route_to_runtime_only: bool = True
    no_frontend_connector_install: bool = True
    no_frontend_connector_execute: bool = True
    no_frontend_secret_storage: bool = True
    no_frontend_workspace_bypass: bool = True
    no_frontend_tool_execution: bool = True
    no_frontend_memory_write: bool = True
    no_frontend_audit_write: bool = True
    no_frontend_rollback_apply: bool = True
    no_raw_endpoint_display: bool = True
    no_mcp_market_install: bool = True
    raw_manifest_inline: bool = False
    read_only_default: bool = True
    quality_gate_required: bool = True
    workspace_authorization_required: bool = True
    runtime_authority_required: bool = True

    @classmethod
    def build(
        cls,
        *,
        display_name: str,
        kind: str = "mcp_server",
        version: str = "0.0.0",
        requested_scopes: List[str] | None = None,
        requested_capabilities: List[str] | None = None,
        manifest_text: str = "",
        source_hint: str = "manual_frontend_request",
        purpose: str = "connector_registry_review",
        run_id: str = "",
        task_id: str = "",
    ) -> "ConnectorRegistrationRequest":
        kind_norm = safe_text(kind, 80)
        if kind_norm not in ALLOWED_CONNECTOR_KINDS:
            raise ValueError("unsupported connector kind")
        manifest_basis = manifest_text or f"{display_name}|{kind_norm}|{version}|{requested_scopes or []}|{requested_capabilities or []}"
        return cls(
            display_name=safe_text(display_name or "未命名连接器", 120),
            kind=kind_norm,
            version=safe_text(version, 60),
            requested_scopes=_safe_list(requested_scopes or ["read_public_metadata"], ALLOWED_CONNECTOR_SCOPES),
            requested_capabilities=[safe_text(x, 80) for x in (requested_capabilities or [])[:12]],
            manifest_digest=digest_text(manifest_basis, 16),
            source_digest=digest_text(source_hint, 16),
            trust_level="unknown",
            default_mode="disabled",
            purpose=safe_text(purpose, 120),
            run_id=safe_text(run_id, 80),
            task_id=safe_text(task_id, 80),
        )

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConnectorRegistrationPublicRecord:
    request_id: str = ""
    display_name: str = ""
    kind: str = "mcp_server"
    status: str = "prepared"
    message: str = ""
    audit_id: str = ""
    manifest_digest: str = ""
    source_digest: str = ""
    signature_digest: str = ""
    trust_level: str = "unknown"
    default_mode: str = "disabled"
    requested_scopes: List[str] = field(default_factory=lambda: ["read_public_metadata"])
    frontend_only_fallback: bool = False
    route_to_runtime_only: bool = True
    quarantined: bool = False
    no_raw_secret_display: bool = True
    no_raw_endpoint_display: bool = True
    no_frontend_install: bool = True
    no_frontend_execute: bool = True

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ConnectorRegistrationPublicRecord":
        payload = data.get("payload", data) if isinstance(data, Mapping) else {}
        if not isinstance(payload, Mapping):
            payload = {}
        return cls(
            request_id=safe_text(payload.get("request_id", payload.get("id", "")), 80),
            display_name=safe_text(payload.get("display_name", payload.get("name", "")), 120),
            kind=safe_text(payload.get("kind", "mcp_server"), 80),
            status=safe_text(payload.get("status", "prepared"), 80),
            message=safe_text(payload.get("message", ""), 220),
            audit_id=safe_text(payload.get("audit_id", payload.get("audit_ref", "")), 80),
            manifest_digest=safe_text(payload.get("manifest_digest", ""), 32),
            source_digest=safe_text(payload.get("source_digest", ""), 32),
            signature_digest=safe_text(payload.get("signature_digest", ""), 32),
            trust_level=safe_text(payload.get("trust_level", "unknown"), 80),
            default_mode=safe_text(payload.get("default_mode", "disabled"), 40),
            requested_scopes=_safe_list(payload.get("requested_scopes", payload.get("scopes", [])), ALLOWED_CONNECTOR_SCOPES),
            frontend_only_fallback=bool(payload.get("frontend_only_fallback", False)),
            route_to_runtime_only=bool(payload.get("route_to_runtime_only", True)),
            quarantined=bool(payload.get("quarantined", False)),
            no_raw_secret_display=bool(payload.get("no_raw_secret_display", True)),
            no_raw_endpoint_display=bool(payload.get("no_raw_endpoint_display", True)),
            no_frontend_install=bool(payload.get("no_frontend_install", True)),
            no_frontend_execute=bool(payload.get("no_frontend_execute", True)),
        )

    @classmethod
    def from_request_result(
        cls,
        request: ConnectorRegistrationRequest,
        *,
        status: str,
        message: str,
        request_id: str = "",
        audit_id: str = "",
        frontend_only_fallback: bool = False,
        quarantined: bool = False,
    ) -> "ConnectorRegistrationPublicRecord":
        return cls(
            request_id=safe_text(request_id, 80),
            display_name=request.display_name,
            kind=request.kind,
            status=safe_text(status, 80),
            message=safe_text(message, 220),
            audit_id=safe_text(audit_id, 80),
            manifest_digest=request.manifest_digest,
            source_digest=request.source_digest,
            signature_digest=request.signature_digest,
            trust_level=request.trust_level,
            default_mode=request.default_mode,
            requested_scopes=request.requested_scopes,
            frontend_only_fallback=frontend_only_fallback,
            quarantined=quarantined,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def connector_registry_policy() -> Dict[str, Any]:
    return {
        "contract_version": CONNECTOR_REGISTRY_CONTRACT_VERSION,
        "registry_endpoint": CONNECTOR_REGISTRY_ENDPOINT,
        "register_endpoint": CONNECTOR_REGISTER_ENDPOINT,
        "quarantine_endpoint": CONNECTOR_QUARANTINE_ENDPOINT,
        "frontend_display_only": True,
        "runtime_authority_required": True,
        "quality_gate_required": True,
        "workspace_authorization_required": True,
        "market_install_disabled": True,
        "unsigned_connector_disabled": True,
        "read_only_default": True,
        "no_frontend_connector_install": True,
        "no_frontend_connector_execute": True,
        "no_frontend_secret_storage": True,
        "no_frontend_workspace_bypass": True,
        "no_raw_endpoint_display": True,
        "no_raw_secret_display": True,
        "allowed_connector_kinds": list(ALLOWED_CONNECTOR_KINDS),
        "allowed_connector_modes": list(ALLOWED_CONNECTOR_MODES),
        "allowed_connector_scopes": list(ALLOWED_CONNECTOR_SCOPES),
    }
