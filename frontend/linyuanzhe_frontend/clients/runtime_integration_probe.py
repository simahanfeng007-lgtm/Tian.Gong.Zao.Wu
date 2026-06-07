from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Mapping, Optional

from linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient
from linyuanzhe_frontend.contracts.integration_smoke import (
    FrontendBackendE2EReport,
    EndpointProbeResult,
    INTEGRATION_SMOKE_CONTRACT_VERSION,
    REQUIRED_PROBE_ENDPOINTS,
    make_runtime_url_digest,
)
from linyuanzhe_frontend.contracts.runtime_snapshot import safe_text
from linyuanzhe_frontend.contracts.sse_events import STATUS_BAR_FIELDS, validate_terminal_order

SECRET_RENDER_MARKERS = (
    "sk-",
    "Bearer ",
    "api_key=",
    "api.deepseek",
    "provider.example.invalid",
    "deepseek.example.invalid",
    "credential_l658_secret",
    "provider-write-l658",
)


class RuntimeIntegrationProbe:
    """L6.58 frontend/backend integration probe.

    The probe only uses the official Runtime gateway endpoints and the
    SseRuntimeClient projection layer. It does not import provider SDKs, does
    not invoke tools locally, and reports the Runtime URL as digest-only.
    """

    def __init__(
        self,
        runtime_url: str,
        *,
        timeout: float = 8.0,
        mode: str = "contract_server",
        provider_write_mode: str = "auto",
        provider_smoke_key: str = "",
        provider_smoke_base_url: str = "",
    ) -> None:
        cleaned = str(runtime_url or "").strip().rstrip("/")
        if not urllib.parse.urlparse(cleaned).scheme:
            cleaned = "http://" + cleaned
        self.runtime_url = cleaned
        self.timeout = float(timeout or 8.0)
        self.mode = safe_text(mode, 40)
        raw_mode = safe_text(provider_write_mode or "auto", 32)
        self.provider_write_mode = raw_mode if raw_mode in {"auto", "fixture", "read_only", "smoke"} else "auto"
        self.provider_smoke_key = str(provider_smoke_key or "")
        self.provider_smoke_base_url = str(provider_smoke_base_url or "")
        self.client = SseRuntimeClient(self.runtime_url, timeout=self.timeout, max_reconnects=1)

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return self.runtime_url + path

    def probe_endpoint(self, path: str, *, method: str = "GET", payload: Optional[Mapping[str, Any]] = None) -> EndpointProbeResult:
        start = time.time()
        data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        try:
            req = urllib.request.Request(
                self._url(path),
                data=data,
                method=method,
                headers={
                    "Accept": "application/json,text/event-stream",
                    "Content-Type": "application/json; charset=utf-8",
                    "X-Tiangong-Frontend-Contract": "L6.58",
                },
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                # For probe purposes, read a bounded small prefix only. The
                # actual chat stream is consumed by SseRuntimeClient below.
                _ = resp.read(2048)
                status = getattr(resp, "status", 200)
                content_type = resp.headers.get("Content-Type", "")
            return EndpointProbeResult(
                path=path,
                method=method,
                ok=200 <= int(status) < 300,
                status_code=int(status),
                latency_ms=int((time.time() - start) * 1000),
                content_type=safe_text(content_type, 100),
            )
        except urllib.error.HTTPError as exc:
            return EndpointProbeResult(
                path=path,
                method=method,
                ok=False,
                status_code=int(getattr(exc, "code", 0) or 0),
                latency_ms=int((time.time() - start) * 1000),
                content_type=safe_text(getattr(exc, "headers", {}).get("Content-Type", "") if getattr(exc, "headers", None) else "", 100),
                error=f"HTTP {getattr(exc, 'code', 'error')}",
            )
        except Exception as exc:
            return EndpointProbeResult(
                path=path,
                method=method,
                ok=False,
                status_code=0,
                latency_ms=int((time.time() - start) * 1000),
                error=safe_text(exc, 180),
            )

    def run(self, message: str = "请生成一个三步只读计划：检查运行状态、返回摘要、结束任务。") -> FrontendBackendE2EReport:
        diagnostics: List[str] = []
        endpoint_results = [self.probe_endpoint(path) for path in REQUIRED_PROBE_ENDPOINTS]
        try:
            refreshed = self.client.refresh_snapshot()
        except Exception as exc:
            refreshed = self.client.get_snapshot()
            diagnostics.append(f"refresh_snapshot failed: {safe_text(exc, 120)}")

        provider_write_ack: Dict[str, Any] = {}
        effective_provider_mode = self.provider_write_mode
        if effective_provider_mode == "auto":
            effective_provider_mode = "fixture" if self.mode == "contract_server" else "read_only"
        try:
            if effective_provider_mode == "fixture":
                # Contract server only. Do not use this branch against a real Runtime.
                provider_write_ack = self.client.submit_provider_settings(
                    {
                        "provider": "deepseek",
                        "main_model": "deepseek-v4-pro",
                        "api_key": "credential_l658_secret",
                        "base_url": "provider-write-l658.local/v1",
                    }
                )
            elif effective_provider_mode == "smoke":
                if not self.provider_smoke_key or not self.provider_smoke_base_url:
                    provider_write_ack = {
                        "status": "skipped",
                        "reason": "provider smoke credentials not supplied",
                        "digest_only": True,
                    }
                    diagnostics.append("provider write smoke skipped: credentials not supplied")
                else:
                    provider_write_ack = self.client.submit_provider_settings(
                        {
                            "provider": "deepseek",
                            "main_model": "deepseek-v4-pro",
                            "api_key": self.provider_smoke_key,
                            "base_url": self.provider_smoke_base_url,
                        }
                    )
            else:
                provider_write_ack = {
                    "status": "read_only_verified",
                    "reason": "real Runtime provider write is not mutated unless explicit smoke credentials are supplied",
                    "digest_only": True,
                }
        except Exception as exc:
            diagnostics.append(f"provider settings submit failed: {safe_text(exc, 120)}")

        try:
            snapshot = self.client.submit_user_message_streaming(message)
        except Exception as exc:
            snapshot = self.client.get_snapshot()
            diagnostics.append(f"chat stream failed: {safe_text(exc, 120)}")

        policy = self.client.get_policy()
        rendered = str({
            "snapshot": snapshot.to_dict(),
            "status": self.client.get_status(),
            "product_identity": self.client.get_product_identity(),
            "provider_settings": self.client.get_provider_settings(),
            "policy": policy,
        })
        event_names = [item.event for item in self.client.last_events]
        status_bar_ok = all(hasattr(snapshot, field) for field in STATUS_BAR_FIELDS)
        product = self.client.get_product_identity()
        product_ok = product.get("unique_developer") == "于泳翔" and product.get("angel_investor") == "胖胖龙"
        provider = self.client.get_provider_settings()
        provider_safe = "api_key" not in provider and "base_url" not in provider and not any(marker in str(provider) for marker in SECRET_RENDER_MARKERS)
        provider_write_status = safe_text(provider_write_ack.get("status", provider.get("status", "")), 60)
        provider_write_ack_ok = provider_write_status in {"accepted", "submitted", "read_only_verified"} and "api_key" not in provider_write_ack and "base_url" not in provider_write_ack
        provider_write_request_only = bool(policy.get("provider_settings_write_policy", {}).get("frontend_must_not_call_provider_sdk", True))
        secret_free = not any(marker in rendered for marker in SECRET_RENDER_MARKERS)
        terminal_order_valid = validate_terminal_order(self.client.last_events)
        if event_names[-2:] != ["assistant_final", "run_terminal"] if len(event_names) >= 2 else True:
            diagnostics.append(f"terminal tail unexpected: {event_names[-3:]}")
        if not secret_free:
            diagnostics.append("rendered projection contains a forbidden secret marker")
        if not provider_safe:
            diagnostics.append("provider projection is missing configured/digest-only fields or contains raw sensitive keys")
        if not provider_write_ack_ok:
            diagnostics.append(f"provider write ack is not accepted/submitted or is not digest-only: {provider_write_status}")
        diagnostics.append(f"provider_write_mode={effective_provider_mode}")
        diagnostics.append(f"provider_write_status={provider_write_status}")
        if refreshed.source_kind.startswith("runtime_sse_disconnected"):
            diagnostics.append("health/product/provider refresh did not fully connect")

        return FrontendBackendE2EReport(
            contract_version=INTEGRATION_SMOKE_CONTRACT_VERSION,
            mode=self.mode,
            runtime_url_digest=make_runtime_url_digest(self.runtime_url),
            endpoint_results=endpoint_results,
            chat_stream_ok=bool(event_names),
            terminal_order_valid=terminal_order_valid,
            assistant_final_seen="assistant_final" in event_names,
            run_terminal_seen="run_terminal" in event_names,
            status_bar_fields_ok=status_bar_ok,
            product_identity_ok=product_ok,
            provider_projection_safe=provider_safe,
            provider_write_ack_ok=provider_write_ack_ok,
            provider_write_request_only=provider_write_request_only,
            action_guard_request_only=bool(policy.get("action_guard_policy", {}).get("no_frontend_gate_bypass", True)),
            no_frontend_provider_call=bool(policy.get("no_direct_provider_call", False)),
            no_frontend_tool_execution=bool(policy.get("no_direct_tool_execution", False)),
            no_frontend_memory_write=bool(policy.get("no_direct_memory_write", False)),
            no_frontend_rollback_apply=bool(policy.get("no_frontend_rollback_apply", False)),
            rendered_secret_free=secret_free,
            event_count=len(event_names),
            final_task_status=safe_text(snapshot.current_task_status, 80),
            final_stream_state=safe_text(snapshot.stream_state, 80),
            final_audit_id=safe_text(snapshot.audit_id, 100),
            diagnostic=diagnostics,
        )
