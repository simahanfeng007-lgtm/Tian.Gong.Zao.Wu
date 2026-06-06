"""Tool action adapter port for L4 phase 4."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .adapter_descriptor import AdapterDescriptor
from .tool_action_failure import ToolActionFailure
from .tool_action_request import ToolActionRequest
from .tool_action_result import ToolActionResult


@runtime_checkable
class ToolActionAdapterPort(Protocol):
    """Protocol only; it does not call a real tool or registry."""

    @property
    def adapter_descriptor(self) -> AdapterDescriptor:
        ...

    def describe(self) -> AdapterDescriptor:
        ...

    def prepare(self, request: ToolActionRequest) -> ToolActionResult | ToolActionFailure:
        ...

    def dry_run_tool_action(self, request: ToolActionRequest) -> ToolActionResult | ToolActionFailure:
        ...

    def invoke(self, request: ToolActionRequest) -> ToolActionResult | ToolActionFailure:
        ...
