"""Disabled real external adapter stubs for L4 phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field

from .adapter_descriptor import AdapterDescriptor
from .adapter_failure import new_adapter_typed_ref
from .adapter_mode import AdapterMode
from .desktop_action_failure import DesktopActionFailure, DesktopActionFailureKind
from .desktop_action_request import DesktopActionRequest
from .external_adapter_common import external_adapter_descriptor
from .file_action_failure import FileActionFailure, FileActionFailureKind
from .file_action_request import FileActionRequest
from .network_action_failure import NetworkActionFailure, NetworkActionFailureKind
from .network_action_request import NetworkActionRequest
from .terminal_action_failure import TerminalActionFailure, TerminalActionFailureKind
from .terminal_action_request import TerminalActionRequest


def _disabled_descriptor(action_kind: str, adapter_kind: str, adapter_name: str, side_effect: str) -> AdapterDescriptor:
    return external_adapter_descriptor(
        adapter_id=f"disabled.real_{action_kind}_adapter_stub",
        adapter_kind=adapter_kind,
        adapter_name=adapter_name,
        action_kind=action_kind,
        envelope_type=f"{action_kind}_request",
        mode=AdapterMode.REAL_STUB,
        side_effect_declared=side_effect,
        resource_usage_declared="future_live_usage_not_enabled",
        audit_requirement_declared="future_audit_requirement_not_enabled",
        requires_l5_permit=True,
        enabled_by_default=False,
        production_enabled=False,
        test_only=False,
    )


@dataclass(frozen=True, slots=True)
class DisabledRealFileAdapterStub:
    adapter_descriptor: AdapterDescriptor = field(
        default_factory=lambda: _disabled_descriptor(
            "file_action",
            "disabled_real_file_stub",
            "Disabled Real File Action Adapter Stub",
            "future_file_side_effect_not_enabled",
        )
    )

    def describe(self) -> AdapterDescriptor:
        return self.adapter_descriptor

    def prepare_file_action(self, request: FileActionRequest) -> FileActionFailure:
        return self.disabled_file_action(request)

    def disabled_file_action(self, request: FileActionRequest) -> FileActionFailure:
        return FileActionFailure(
            failure_ref=new_adapter_typed_ref("file_action_failure"),
            request_ref=request.request_ref,
            failure_kind=FileActionFailureKind.DISABLED_BY_DEFAULT,
            message="real file action is disabled in L4 phase 5",
            blocked_invariant_names=("ExternalActionDisabledByDefault", "NoRealFileSystemMutationInvariant"),
            real_file_read=False,
            real_file_mutation=False,
        )


@dataclass(frozen=True, slots=True)
class DisabledRealNetworkAdapterStub:
    adapter_descriptor: AdapterDescriptor = field(
        default_factory=lambda: _disabled_descriptor(
            "network_action",
            "disabled_real_network_stub",
            "Disabled Real Network Action Adapter Stub",
            "future_network_side_effect_not_enabled",
        )
    )

    def describe(self) -> AdapterDescriptor:
        return self.adapter_descriptor

    def prepare_network_action(self, request: NetworkActionRequest) -> NetworkActionFailure:
        return self.disabled_network_action(request)

    def disabled_network_action(self, request: NetworkActionRequest) -> NetworkActionFailure:
        return NetworkActionFailure(
            failure_ref=new_adapter_typed_ref("network_action_failure"),
            request_ref=request.request_ref,
            failure_kind=NetworkActionFailureKind.DISABLED_BY_DEFAULT,
            message="real network action is disabled in L4 phase 5",
            blocked_invariant_names=("ExternalActionDisabledByDefault", "NoRealNetworkAccessInvariant"),
            real_network_access=False,
            sends_payload=False,
        )


@dataclass(frozen=True, slots=True)
class DisabledRealTerminalAdapterStub:
    adapter_descriptor: AdapterDescriptor = field(
        default_factory=lambda: _disabled_descriptor(
            "terminal_action",
            "disabled_real_terminal_stub",
            "Disabled Real Terminal Action Adapter Stub",
            "future_terminal_side_effect_not_enabled",
        )
    )

    def describe(self) -> AdapterDescriptor:
        return self.adapter_descriptor

    def prepare_terminal_action(self, request: TerminalActionRequest) -> TerminalActionFailure:
        return self.disabled_terminal_action(request)

    def disabled_terminal_action(self, request: TerminalActionRequest) -> TerminalActionFailure:
        return TerminalActionFailure(
            failure_ref=new_adapter_typed_ref("terminal_action_failure"),
            request_ref=request.request_ref,
            failure_kind=TerminalActionFailureKind.DISABLED_BY_DEFAULT,
            message="real terminal action is disabled in L4 phase 5",
            blocked_invariant_names=("ExternalActionDisabledByDefault", "NoRealShellExecutionInvariant"),
            real_command_executed=False,
            process_started=False,
            privilege_escalated=False,
        )


@dataclass(frozen=True, slots=True)
class DisabledRealDesktopAdapterStub:
    adapter_descriptor: AdapterDescriptor = field(
        default_factory=lambda: _disabled_descriptor(
            "desktop_action",
            "disabled_real_desktop_stub",
            "Disabled Real Desktop Action Adapter Stub",
            "future_desktop_side_effect_not_enabled",
        )
    )

    def describe(self) -> AdapterDescriptor:
        return self.adapter_descriptor

    def prepare_desktop_action(self, request: DesktopActionRequest) -> DesktopActionFailure:
        return self.disabled_desktop_action(request)

    def disabled_desktop_action(self, request: DesktopActionRequest) -> DesktopActionFailure:
        return DesktopActionFailure(
            failure_ref=new_adapter_typed_ref("desktop_action_failure"),
            request_ref=request.request_ref,
            failure_kind=DesktopActionFailureKind.DISABLED_BY_DEFAULT,
            message="real desktop action is disabled in L4 phase 5",
            blocked_invariant_names=("ExternalActionDisabledByDefault", "NoRealDesktopControlInvariant"),
            real_desktop_control=False,
            real_screen_access=False,
            real_input_sent=False,
        )
