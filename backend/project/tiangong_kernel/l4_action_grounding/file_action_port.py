"""File action adapter port for L4 phase 5."""

from __future__ import annotations

from typing import Protocol

from .adapter_descriptor import AdapterDescriptor
from .file_action_failure import FileActionFailure
from .file_action_request import FileActionRequest
from .file_action_result import FileActionResult


class FileActionAdapterPort(Protocol):
    """Protocol only; future live file capability belongs outside L4."""

    def describe(self) -> AdapterDescriptor:
        ...

    def prepare_file_action(self, request: FileActionRequest) -> FileActionResult | FileActionFailure:
        ...
