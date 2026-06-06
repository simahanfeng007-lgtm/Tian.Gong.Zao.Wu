"""Dry-run terminal adapter for L4 phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field

from .adapter_descriptor import AdapterDescriptor
from .adapter_failure import new_adapter_typed_ref
from .adapter_mode import AdapterMode
from .external_adapter_common import external_adapter_descriptor
from .terminal_action_failure import TerminalActionFailure
from .terminal_action_request import TerminalActionRequest
from .terminal_action_result import TerminalActionResult


def _dry_run_terminal_descriptor() -> AdapterDescriptor:
    return external_adapter_descriptor(
        adapter_id="dry_run.terminal_action_adapter",
        adapter_kind="dry_run_terminal",
        adapter_name="Dry Run Terminal Action Adapter",
        action_kind="terminal_action",
        envelope_type="terminal_action_request",
        mode=AdapterMode.DRY_RUN,
        side_effect_declared="preview_only",
        resource_usage_declared="dry_run_preview_only",
        audit_requirement_declared="future_audit_requirement_ref",
        supports_dry_run=True,
    )


@dataclass(frozen=True, slots=True)
class DryRunTerminalAdapter:
    """Preview adapter; it starts no process."""

    adapter_descriptor: AdapterDescriptor = field(default_factory=_dry_run_terminal_descriptor)

    def describe(self) -> AdapterDescriptor:
        return self.adapter_descriptor

    def prepare_terminal_action(self, request: TerminalActionRequest) -> TerminalActionResult | TerminalActionFailure:
        return self.dry_run_terminal_action(request)

    def dry_run_terminal_action(self, request: TerminalActionRequest) -> TerminalActionResult:
        return TerminalActionResult(
            result_ref=new_adapter_typed_ref("terminal_action_result"),
            request_ref=request.request_ref,
            stdout_ref=new_adapter_typed_ref("terminal_dry_run_stdout"),
            resource_usage_summary=request.resource_usage.summary,
            payload_items=(("mode", "dry_run"), ("process_started", "false")),
            dry_run_only=True,
            real_command_executed=False,
            process_started=False,
        )
