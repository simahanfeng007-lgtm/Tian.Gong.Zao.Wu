"""Desktop action adapter port for L4 phase 5."""

from __future__ import annotations

from typing import Protocol

from .adapter_descriptor import AdapterDescriptor
from .desktop_action_failure import DesktopActionFailure
from .desktop_action_request import DesktopActionRequest
from .desktop_action_result import DesktopActionResult


class DesktopActionAdapterPort(Protocol):
    """Protocol only; live UI capability is reserved for a future layer."""

    def describe(self) -> AdapterDescriptor:
        ...

    def prepare_desktop_action(self, request: DesktopActionRequest) -> DesktopActionResult | DesktopActionFailure:
        ...
