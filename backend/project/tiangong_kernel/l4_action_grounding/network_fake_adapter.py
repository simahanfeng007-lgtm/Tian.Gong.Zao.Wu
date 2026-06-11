"""Fake network adapter for L4 phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field

from .adapter_descriptor import AdapterDescriptor
from .adapter_failure import new_adapter_typed_ref
from .adapter_mode import AdapterMode
from .external_adapter_common import external_adapter_descriptor
from .network_action_failure import NetworkActionFailure
from .network_action_request import NetworkActionRequest
from .network_action_result import NetworkActionResult


def _fake_network_descriptor() -> AdapterDescriptor:
    return external_adapter_descriptor(
        adapter_id="fake.network_action_adapter",
        adapter_kind="fake_network",
        adapter_name="Fake Network Action Adapter",
        action_kind="network_action",
        envelope_type="network_action_request",
        mode=AdapterMode.FAKE,
        side_effect_declared="none",
        resource_usage_declared="fake_usage_only",
        audit_requirement_declared="test_trace_only",
        supports_fake=True,
        test_only=True,
    )


@dataclass(frozen=True, slots=True)
class FakeNetworkAdapter:
    """Deterministic test adapter; it performs no network access."""

    adapter_descriptor: AdapterDescriptor = field(default_factory=_fake_network_descriptor)

    def describe(self) -> AdapterDescriptor:
        return self.adapter_descriptor

    def prepare_network_action(self, request: NetworkActionRequest) -> NetworkActionResult | NetworkActionFailure:
        return self.fake_network_action(request)

    def fake_network_action(self, request: NetworkActionRequest) -> NetworkActionResult:
        return NetworkActionResult(
            result_ref=new_adapter_typed_ref("network_action_result"),
            request_ref=request.request_ref,
            response_ref=new_adapter_typed_ref("network_response"),
            status_ref=new_adapter_typed_ref("network_status"),
            observation_ref=new_adapter_typed_ref("network_observation"),
            usage_summary="fake_usage_only",
            payload_items=(("network_result", "fake"), ("real_network_access", "false")),
            fake_result=True,
            real_network_access=False,
            caches_real_response_body=False,
        )
