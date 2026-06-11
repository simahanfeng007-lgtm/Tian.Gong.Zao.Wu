"""No-op adapters for L4 phase 5 external actions."""

from __future__ import annotations

from dataclasses import dataclass, field

from .adapter_descriptor import AdapterDescriptor
from .adapter_failure import new_adapter_typed_ref
from .adapter_mode import AdapterMode
from .desktop_action_failure import DesktopActionFailure
from .desktop_action_request import DesktopActionRequest
from .desktop_action_result import DesktopActionResult
from .external_adapter_common import external_adapter_descriptor
from .file_action_failure import FileActionFailure
from .file_action_request import FileActionRequest
from .file_action_result import FileActionResult
from .network_action_failure import NetworkActionFailure
from .network_action_request import NetworkActionRequest
from .network_action_result import NetworkActionResult
from .terminal_action_failure import TerminalActionFailure
from .terminal_action_request import TerminalActionRequest
from .terminal_action_result import TerminalActionResult


def _no_op_descriptor(action_kind: str, adapter_kind: str, adapter_name: str) -> AdapterDescriptor:
    return external_adapter_descriptor(
        adapter_id=f"no_op.{action_kind}_adapter",
        adapter_kind=adapter_kind,
        adapter_name=adapter_name,
        action_kind=action_kind,
        envelope_type=f"{action_kind}_request",
        mode=AdapterMode.NO_OP,
        side_effect_declared="none",
        resource_usage_declared="none",
        audit_requirement_declared="none",
        supports_no_op=True,
    )


@dataclass(frozen=True, slots=True)
class NoOpFileAdapter:
    adapter_descriptor: AdapterDescriptor = field(default_factory=lambda: _no_op_descriptor("file_action", "no_op_file", "No Op File Action Adapter"))

    def describe(self) -> AdapterDescriptor:
        return self.adapter_descriptor

    def prepare_file_action(self, request: FileActionRequest) -> FileActionResult | FileActionFailure:
        return FileActionResult(
            result_ref=new_adapter_typed_ref("file_action_result"),
            request_ref=request.request_ref,
            output_ref=new_adapter_typed_ref("file_no_op_output"),
            side_effect_summary="none",
            resource_usage_summary="none",
            payload_items=(("mode", "no_op"),),
            no_op_result=True,
            real_file_read=False,
            real_file_mutation=False,
        )


@dataclass(frozen=True, slots=True)
class NoOpNetworkAdapter:
    adapter_descriptor: AdapterDescriptor = field(default_factory=lambda: _no_op_descriptor("network_action", "no_op_network", "No Op Network Action Adapter"))

    def describe(self) -> AdapterDescriptor:
        return self.adapter_descriptor

    def prepare_network_action(self, request: NetworkActionRequest) -> NetworkActionResult | NetworkActionFailure:
        return NetworkActionResult(
            result_ref=new_adapter_typed_ref("network_action_result"),
            request_ref=request.request_ref,
            response_ref=new_adapter_typed_ref("network_no_op_response"),
            usage_summary="none",
            payload_items=(("mode", "no_op"),),
            no_op_result=True,
            real_network_access=False,
            caches_real_response_body=False,
        )


@dataclass(frozen=True, slots=True)
class NoOpTerminalAdapter:
    adapter_descriptor: AdapterDescriptor = field(default_factory=lambda: _no_op_descriptor("terminal_action", "no_op_terminal", "No Op Terminal Action Adapter"))

    def describe(self) -> AdapterDescriptor:
        return self.adapter_descriptor

    def prepare_terminal_action(self, request: TerminalActionRequest) -> TerminalActionResult | TerminalActionFailure:
        return TerminalActionResult(
            result_ref=new_adapter_typed_ref("terminal_action_result"),
            request_ref=request.request_ref,
            stdout_ref=new_adapter_typed_ref("terminal_no_op_stdout"),
            resource_usage_summary="none",
            payload_items=(("mode", "no_op"),),
            no_op_result=True,
            real_command_executed=False,
            process_started=False,
        )


@dataclass(frozen=True, slots=True)
class NoOpDesktopAdapter:
    adapter_descriptor: AdapterDescriptor = field(default_factory=lambda: _no_op_descriptor("desktop_action", "no_op_desktop", "No Op Desktop Action Adapter"))

    def describe(self) -> AdapterDescriptor:
        return self.adapter_descriptor

    def prepare_desktop_action(self, request: DesktopActionRequest) -> DesktopActionResult | DesktopActionFailure:
        return DesktopActionResult(
            result_ref=new_adapter_typed_ref("desktop_action_result"),
            request_ref=request.request_ref,
            ui_observation_ref=new_adapter_typed_ref("desktop_no_op_observation"),
            resource_usage_summary="none",
            payload_items=(("mode", "no_op"),),
            no_op_result=True,
            real_desktop_control=False,
            real_screen_access=False,
            real_input_sent=False,
        )
