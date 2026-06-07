"""Terminal action adapter port for L4 phase 5."""

from __future__ import annotations

from typing import Protocol

from .adapter_descriptor import AdapterDescriptor
from .terminal_action_failure import TerminalActionFailure
from .terminal_action_request import TerminalActionRequest
from .terminal_action_result import TerminalActionResult


class TerminalActionAdapterPort(Protocol):
    """Protocol only; live command capability is reserved for a future layer."""

    def describe(self) -> AdapterDescriptor:
        ...

    def prepare_terminal_action(self, request: TerminalActionRequest) -> TerminalActionResult | TerminalActionFailure:
        ...
