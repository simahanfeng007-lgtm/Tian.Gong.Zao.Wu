"""Fake terminal adapter for L4 phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field

from .adapter_descriptor import AdapterDescriptor
from .adapter_failure import new_adapter_typed_ref
from .adapter_mode import AdapterMode
from .external_adapter_common import external_adapter_descriptor
from .terminal_action_failure import TerminalActionFailure
from .terminal_action_request import TerminalActionRequest
from .terminal_action_result import TerminalActionResult


def _fake_terminal_descriptor() -> AdapterDescriptor:
    return external_adapter_descriptor(
        adapter_id="fake.terminal_action_adapter",
        adapter_kind="fake_terminal",
        adapter_name="Fake Terminal Action Adapter",
        action_kind="terminal_action",
        envelope_type="terminal_action_request",
        mode=AdapterMode.FAKE,
        side_effect_declared="none",
        resource_usage_declared="fake_usage_only",
        audit_requirement_declared="test_trace_only",
        supports_fake=True,
        test_only=True,
    )


@dataclass(frozen=True, slots=True)
class FakeTerminalAdapter:
    """Deterministic test adapter; it starts no process."""

    adapter_descriptor: AdapterDescriptor = field(default_factory=_fake_terminal_descriptor)

    def describe(self) -> AdapterDescriptor:
        return self.adapter_descriptor

    def prepare_terminal_action(self, request: TerminalActionRequest) -> TerminalActionResult | TerminalActionFailure:
        return self.fake_terminal_action(request)

    def fake_terminal_action(self, request: TerminalActionRequest) -> TerminalActionResult:
        return TerminalActionResult(
            result_ref=new_adapter_typed_ref("terminal_action_result"),
            request_ref=request.request_ref,
            stdout_ref=new_adapter_typed_ref("terminal_stdout"),
            stderr_ref=new_adapter_typed_ref("terminal_stderr"),
            exit_code_ref=new_adapter_typed_ref("terminal_exit_code"),
            resource_usage_summary="fake_usage_only",
            payload_items=(("terminal_result", "fake"), ("process_started", "false")),
            fake_result=True,
            real_command_executed=False,
            process_started=False,
        )
