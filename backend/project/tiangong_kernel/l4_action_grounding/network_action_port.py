"""Network action adapter port for L4 phase 5."""

from __future__ import annotations

from typing import Protocol

from .adapter_descriptor import AdapterDescriptor
from .network_action_failure import NetworkActionFailure
from .network_action_request import NetworkActionRequest
from .network_action_result import NetworkActionResult


class NetworkActionAdapterPort(Protocol):
    """Protocol only; live network capability is reserved for a future layer."""

    def describe(self) -> AdapterDescriptor:
        ...

    def prepare_network_action(self, request: NetworkActionRequest) -> NetworkActionResult | NetworkActionFailure:
        ...
