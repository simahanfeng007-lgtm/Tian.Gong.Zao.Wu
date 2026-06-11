from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping

try:
    from .runtime_snapshot import digest_text, safe_text
    from .sse_events import (
        CHAT_STREAM_ENDPOINT,
        HEALTH_ENDPOINT,
        PRODUCT_METADATA_ENDPOINT,
        PROVIDER_SETTINGS_ENDPOINT,
        STATUS_BAR_FIELDS,
    )
except ImportError:  # direct script smoke execution
    from linyuanzhe_frontend.contracts.runtime_snapshot import digest_text, safe_text
    from linyuanzhe_frontend.contracts.sse_events import (
        CHAT_STREAM_ENDPOINT,
        HEALTH_ENDPOINT,
        PRODUCT_METADATA_ENDPOINT,
        PROVIDER_SETTINGS_ENDPOINT,
        STATUS_BAR_FIELDS,
    )

INTEGRATION_SMOKE_CONTRACT_VERSION = "tiangong.l6_73_8.frontend_backend_e2e_smoke.v1"
INTEGRATION_ALLOWED_ENDPOINTS = (
    HEALTH_ENDPOINT,
    PRODUCT_METADATA_ENDPOINT,
    PROVIDER_SETTINGS_ENDPOINT,
    CHAT_STREAM_ENDPOINT,
    "/tasks/stop",
    "/tasks/reset",
    "/confirmations/submit",
)
REQUIRED_PROBE_ENDPOINTS = (
    HEALTH_ENDPOINT,
    PRODUCT_METADATA_ENDPOINT,
    PROVIDER_SETTINGS_ENDPOINT,
)
REQUIRED_TERMINAL_TAIL = ("assistant_final", "run_terminal")


@dataclass(frozen=True)
class EndpointProbeResult:
    path: str
    method: str = "GET"
    ok: bool = False
    status_code: int = 0
    latency_ms: int = 0
    content_type: str = ""
    error: str = ""

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "EndpointProbeResult":
        return cls(
            path=safe_text(data.get("path", ""), 100),
            method=safe_text(data.get("method", "GET"), 12),
            ok=bool(data.get("ok", False)),
            status_code=_safe_int(data.get("status_code"), 0),
            latency_ms=_safe_int(data.get("latency_ms"), 0),
            content_type=safe_text(data.get("content_type", ""), 100),
            error=safe_text(data.get("error", ""), 180),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "method": self.method,
            "ok": self.ok,
            "status_code": self.status_code,
            "latency_ms": self.latency_ms,
            "content_type": self.content_type,
            "error": self.error,
        }


@dataclass(frozen=True)
class FrontendBackendE2EReport:
    contract_version: str = INTEGRATION_SMOKE_CONTRACT_VERSION
    mode: str = "contract_server"
    runtime_url_digest: str = ""
    endpoint_results: List[EndpointProbeResult] = field(default_factory=list)
    chat_stream_ok: bool = False
    terminal_order_valid: bool = False
    assistant_final_seen: bool = False
    run_terminal_seen: bool = False
    status_bar_fields_ok: bool = False
    product_identity_ok: bool = False
    provider_projection_safe: bool = False
    provider_write_ack_ok: bool = False
    provider_write_request_only: bool = True
    action_guard_request_only: bool = True
    no_frontend_provider_call: bool = True
    no_frontend_tool_execution: bool = True
    no_frontend_memory_write: bool = True
    no_frontend_rollback_apply: bool = True
    rendered_secret_free: bool = True
    event_count: int = 0
    final_task_status: str = ""
    final_stream_state: str = ""
    final_audit_id: str = ""
    diagnostic: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return (
            bool(self.endpoint_results)
            and all(item.ok for item in self.endpoint_results)
            and self.chat_stream_ok
            and self.terminal_order_valid
            and self.assistant_final_seen
            and self.run_terminal_seen
            and self.status_bar_fields_ok
            and self.product_identity_ok
            and self.provider_projection_safe
            and self.provider_write_ack_ok
            and self.provider_write_request_only
            and self.action_guard_request_only
            and self.no_frontend_provider_call
            and self.no_frontend_tool_execution
            and self.no_frontend_memory_write
            and self.no_frontend_rollback_apply
            and self.rendered_secret_free
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "mode": self.mode,
            "runtime_url_digest": self.runtime_url_digest,
            "endpoint_results": [item.to_dict() for item in self.endpoint_results],
            "chat_stream_ok": self.chat_stream_ok,
            "terminal_order_valid": self.terminal_order_valid,
            "assistant_final_seen": self.assistant_final_seen,
            "run_terminal_seen": self.run_terminal_seen,
            "status_bar_fields_ok": self.status_bar_fields_ok,
            "product_identity_ok": self.product_identity_ok,
            "provider_projection_safe": self.provider_projection_safe,
            "provider_write_ack_ok": self.provider_write_ack_ok,
            "provider_write_request_only": self.provider_write_request_only,
            "action_guard_request_only": self.action_guard_request_only,
            "no_frontend_provider_call": self.no_frontend_provider_call,
            "no_frontend_tool_execution": self.no_frontend_tool_execution,
            "no_frontend_memory_write": self.no_frontend_memory_write,
            "no_frontend_rollback_apply": self.no_frontend_rollback_apply,
            "rendered_secret_free": self.rendered_secret_free,
            "event_count": self.event_count,
            "final_task_status": self.final_task_status,
            "final_stream_state": self.final_stream_state,
            "final_audit_id": self.final_audit_id,
            "diagnostic": list(self.diagnostic),
            "ok": self.ok,
        }



def make_runtime_url_digest(value: Any) -> str:
    return digest_text(value, 16) if str(value or "").strip() else ""



def integration_smoke_policy() -> Dict[str, Any]:
    return {
        "contract_version": INTEGRATION_SMOKE_CONTRACT_VERSION,
        "allowed_endpoints": list(INTEGRATION_ALLOWED_ENDPOINTS),
        "required_probe_endpoints": list(REQUIRED_PROBE_ENDPOINTS),
        "required_status_bar_fields": list(STATUS_BAR_FIELDS),
        "required_terminal_tail": list(REQUIRED_TERMINAL_TAIL),
        "frontend_role": "display_submit_request_only",
        "no_direct_provider_call": True,
        "no_direct_tool_execution": True,
        "no_direct_memory_write": True,
        "no_frontend_audit_write": True,
        "no_frontend_rollback_apply": True,
        "no_kernel_mutation": True,
        "runtime_url_in_reports": "digest_only",
        "provider_settings_endpoint": PROVIDER_SETTINGS_ENDPOINT,
        "provider_settings_write_method": "POST",
        "provider_settings_write_only_fields": ["api_key"],
        "provider_settings_base_url_display": "visible_in_settings",
    }



def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def main() -> int:
    policy = integration_smoke_policy()
    assert policy["frontend_role"] == "display_submit_request_only"
    assert policy["no_direct_provider_call"] is True
    assert policy["no_direct_tool_execution"] is True
    assert CHAT_STREAM_ENDPOINT in policy["allowed_endpoints"]
    assert set(REQUIRED_TERMINAL_TAIL) == {"assistant_final", "run_terminal"}
    print("PASS frontend_backend_integration_contract_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
