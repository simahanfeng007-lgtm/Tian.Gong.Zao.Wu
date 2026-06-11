from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping

from .integration_smoke import FrontendBackendE2EReport, INTEGRATION_ALLOWED_ENDPOINTS
from .runtime_snapshot import safe_text

RC_PREFLIGHT_CONTRACT_VERSION = "tiangong.l6_73_8.frontend_backend_rc_preflight.v1"
RC_READY_STATUS = "ready_for_frontend_backend_combine"
RC_BLOCKED_STATUS = "blocked_before_frontend_backend_combine"
RC_FAILED_STATUS = "failed_before_frontend_backend_combine"


@dataclass(frozen=True)
class RcPreflightReport:
    """Frontend/backend RC preflight gate for FE01 STEP68 / L6.73.8.

    A contract-server run proves that the desktop package remains regression-safe.
    It does not prove that a user's real TiangongWangguan/Runtime instance is live.
    Therefore formal frontend/backend combine is allowed only when a real runtime
    URL was provided and the real integration report is green.
    """

    contract_version: str = RC_PREFLIGHT_CONTRACT_VERSION
    mode: str = "contract_server"
    real_runtime_requested: bool = False
    real_runtime_executed: bool = False
    contract_server_fallback_used: bool = True
    real_runtime_skipped_reason: str = "LINYUANZHE_RUNTIME_URL not provided"
    integration_report: Dict[str, Any] = field(default_factory=dict)
    endpoint_contract_ok: bool = False
    provider_write_ack_ok: bool = False
    provider_write_digest_only: bool = False
    chat_stream_terminal_ok: bool = False
    product_identity_ok: bool = False
    status_bar_ok: bool = False
    secret_free: bool = False
    frontend_boundary_ok: bool = False
    rc_status: str = RC_BLOCKED_STATUS
    merge_blockers: List[str] = field(default_factory=list)
    next_action: str = "Start real TiangongWangguan/Runtime and rerun with LINYUANZHE_RUNTIME_URL."

    @classmethod
    def from_integration_report(
        cls,
        report: FrontendBackendE2EReport | Mapping[str, Any],
        *,
        mode: str,
        real_runtime_requested: bool,
        real_runtime_executed: bool,
        contract_server_fallback_used: bool,
        real_runtime_skipped_reason: str = "",
    ) -> "RcPreflightReport":
        payload = report.to_dict() if isinstance(report, FrontendBackendE2EReport) else dict(report)
        endpoint_contract_ok = bool(payload.get("endpoint_results")) and all(bool(item.get("ok")) for item in payload.get("endpoint_results", []))
        provider_write_ack_ok = bool(payload.get("provider_write_ack_ok", False))
        provider_write_digest_only = bool(payload.get("provider_projection_safe", False)) and bool(payload.get("rendered_secret_free", False))
        chat_stream_terminal_ok = bool(payload.get("chat_stream_ok", False)) and bool(payload.get("terminal_order_valid", False)) and bool(payload.get("assistant_final_seen", False)) and bool(payload.get("run_terminal_seen", False))
        product_identity_ok = bool(payload.get("product_identity_ok", False))
        status_bar_ok = bool(payload.get("status_bar_fields_ok", False))
        secret_free = bool(payload.get("rendered_secret_free", False))
        frontend_boundary_ok = all(
            bool(payload.get(key, False))
            for key in (
                "provider_write_request_only",
                "action_guard_request_only",
                "no_frontend_provider_call",
                "no_frontend_tool_execution",
                "no_frontend_memory_write",
                "no_frontend_rollback_apply",
            )
        )
        merge_blockers: List[str] = []
        if not endpoint_contract_ok:
            merge_blockers.append("required Runtime endpoints did not all pass")
        if not provider_write_ack_ok:
            merge_blockers.append("Provider settings write acknowledgement did not pass")
        if not provider_write_digest_only:
            merge_blockers.append("Provider projection is not digest-only or rendered output is not secret-free")
        if not chat_stream_terminal_ok:
            merge_blockers.append("chat stream did not complete assistant_final -> run_terminal")
        if not product_identity_ok:
            merge_blockers.append("product identity metadata mismatch")
        if not status_bar_ok:
            merge_blockers.append("bottom status bar 9-field contract mismatch")
        if not secret_free:
            merge_blockers.append("rendered report contains forbidden secret marker")
        if not frontend_boundary_ok:
            merge_blockers.append("frontend boundary flags are not all request/display-only")
        if not real_runtime_executed:
            merge_blockers.append("real Runtime instance smoke not executed")

        integration_ok = bool(payload.get("ok", False))
        rc_ready = integration_ok and real_runtime_executed and not merge_blockers
        if rc_ready:
            rc_status = RC_READY_STATUS
            next_action = "Proceed to FE01 STEP20 / L6.59 frontend-backend combined RC package."
        elif integration_ok and contract_server_fallback_used:
            rc_status = RC_BLOCKED_STATUS
            next_action = "Start real TiangongWangguan/Runtime and rerun RC preflight with LINYUANZHE_RUNTIME_URL."
        else:
            rc_status = RC_FAILED_STATUS
            next_action = "Fix failing endpoint/settings/stream/boundary checks before combine."

        return cls(
            mode=safe_text(mode, 40),
            real_runtime_requested=real_runtime_requested,
            real_runtime_executed=real_runtime_executed,
            contract_server_fallback_used=contract_server_fallback_used,
            real_runtime_skipped_reason=safe_text(real_runtime_skipped_reason, 180),
            integration_report=payload,
            endpoint_contract_ok=endpoint_contract_ok,
            provider_write_ack_ok=provider_write_ack_ok,
            provider_write_digest_only=provider_write_digest_only,
            chat_stream_terminal_ok=chat_stream_terminal_ok,
            product_identity_ok=product_identity_ok,
            status_bar_ok=status_bar_ok,
            secret_free=secret_free,
            frontend_boundary_ok=frontend_boundary_ok,
            rc_status=rc_status,
            merge_blockers=merge_blockers,
            next_action=next_action,
        )

    @property
    def ready_for_combine(self) -> bool:
        return self.rc_status == RC_READY_STATUS

    @property
    def ok(self) -> bool:
        # A contract-server fallback may be regression-green but still blocked
        # for formal combine. The script treats both as a successful preflight
        # artifact unless --require-real is used.
        return self.rc_status in {RC_READY_STATUS, RC_BLOCKED_STATUS}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "mode": self.mode,
            "real_runtime_requested": self.real_runtime_requested,
            "real_runtime_executed": self.real_runtime_executed,
            "contract_server_fallback_used": self.contract_server_fallback_used,
            "real_runtime_skipped_reason": self.real_runtime_skipped_reason,
            "endpoint_contract_ok": self.endpoint_contract_ok,
            "provider_write_ack_ok": self.provider_write_ack_ok,
            "provider_write_digest_only": self.provider_write_digest_only,
            "chat_stream_terminal_ok": self.chat_stream_terminal_ok,
            "product_identity_ok": self.product_identity_ok,
            "status_bar_ok": self.status_bar_ok,
            "secret_free": self.secret_free,
            "frontend_boundary_ok": self.frontend_boundary_ok,
            "ready_for_combine": self.ready_for_combine,
            "rc_status": self.rc_status,
            "merge_blockers": list(self.merge_blockers),
            "next_action": self.next_action,
            "integration_report": dict(self.integration_report),
            "ok": self.ok,
        }


def rc_preflight_policy() -> Dict[str, Any]:
    return {
        "contract_version": RC_PREFLIGHT_CONTRACT_VERSION,
        "formal_combine_requires_real_runtime": True,
        "contract_server_fallback_allowed_for_regression": True,
        "allowed_endpoints": list(INTEGRATION_ALLOWED_ENDPOINTS),
        "runtime_url_in_reports": "digest_only",
        "frontend_role": "display_submit_request_only",
        "must_pass_before_step20": [
            "real_runtime_executed",
            "endpoint_contract_ok",
            "provider_write_ack_ok",
            "provider_write_digest_only",
            "chat_stream_terminal_ok",
            "product_identity_ok",
            "status_bar_ok",
            "secret_free",
            "frontend_boundary_ok",
        ],
    }
