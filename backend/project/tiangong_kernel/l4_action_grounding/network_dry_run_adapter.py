"""Dry-run network adapter for L4 phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field

from .adapter_descriptor import AdapterDescriptor
from .adapter_failure import new_adapter_typed_ref
from .adapter_mode import AdapterMode
from .external_adapter_common import external_adapter_descriptor
from .network_action_failure import NetworkActionFailure
from .network_action_request import NetworkActionRequest
from .network_action_result import NetworkActionResult


def _dry_run_network_descriptor() -> AdapterDescriptor:
    return external_adapter_descriptor(
        adapter_id="dry_run.network_action_adapter",
        adapter_kind="dry_run_network",
        adapter_name="Dry Run Network Action Adapter",
        action_kind="network_action",
        envelope_type="network_action_request",
        mode=AdapterMode.DRY_RUN,
        side_effect_declared="preview_only",
        resource_usage_declared="dry_run_preview_only",
        audit_requirement_declared="future_audit_requirement_ref",
        supports_dry_run=True,
    )


@dataclass(frozen=True, slots=True)
class DryRunNetworkAdapter:
    """Preview adapter; it performs no network access."""

    adapter_descriptor: AdapterDescriptor = field(default_factory=_dry_run_network_descriptor)

    def describe(self) -> AdapterDescriptor:
        return self.adapter_descriptor

    def prepare_network_action(self, request: NetworkActionRequest) -> NetworkActionResult | NetworkActionFailure:
        return self.dry_run_network_action(request)

    def dry_run_network_action(self, request: NetworkActionRequest) -> NetworkActionResult:
        return NetworkActionResult(
            result_ref=new_adapter_typed_ref("network_action_result"),
            request_ref=request.request_ref,
            response_ref=new_adapter_typed_ref("network_dry_run_response"),
            usage_summary=request.resource_usage.summary,
            payload_items=(("mode", "dry_run"), ("real_network_access", "false")),
            dry_run_only=True,
            real_network_access=False,
            caches_real_response_body=False,
        )
