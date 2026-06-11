"""Normalization helpers for phase 5 external action envelopes."""

from __future__ import annotations

from dataclasses import dataclass

from .desktop_action_failure import DesktopActionFailure
from .desktop_action_result import DesktopActionResult
from .file_action_failure import FileActionFailure
from .file_action_result import FileActionResult
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_schema_version, ensure_true
from .network_action_failure import NetworkActionFailure
from .network_action_result import NetworkActionResult
from .terminal_action_failure import TerminalActionFailure
from .terminal_action_result import TerminalActionResult


@dataclass(frozen=True, slots=True)
class ExternalActionNormalization:
    """Normalize local phase 5 envelopes only; no state or audit store is written."""

    normalization_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.normalization_only, "ExternalActionNormalization.normalization_only")
        ensure_schema_version(self.schema_version, "ExternalActionNormalization.schema_version")

    def result_kind(self, result: FileActionResult | NetworkActionResult | TerminalActionResult | DesktopActionResult) -> str:
        if isinstance(result, FileActionResult):
            return "file_action_result"
        if isinstance(result, NetworkActionResult):
            return "network_action_result"
        if isinstance(result, TerminalActionResult):
            return "terminal_action_result"
        if isinstance(result, DesktopActionResult):
            return "desktop_action_result"
        raise TypeError("unsupported external action result")

    def failure_kind(self, failure: FileActionFailure | NetworkActionFailure | TerminalActionFailure | DesktopActionFailure) -> str:
        if isinstance(failure, FileActionFailure):
            return failure.failure_kind.value
        if isinstance(failure, NetworkActionFailure):
            return failure.failure_kind.value
        if isinstance(failure, TerminalActionFailure):
            return failure.failure_kind.value
        if isinstance(failure, DesktopActionFailure):
            return failure.failure_kind.value
        raise TypeError("unsupported external action failure")
