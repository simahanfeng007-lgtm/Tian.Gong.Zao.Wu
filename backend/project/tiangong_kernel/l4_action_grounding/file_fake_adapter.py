"""Fake file adapter for L4 phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field

from .adapter_descriptor import AdapterDescriptor
from .adapter_failure import new_adapter_typed_ref
from .adapter_mode import AdapterMode
from .external_adapter_common import external_adapter_descriptor
from .file_action_failure import FileActionFailure
from .file_action_request import FileActionRequest
from .file_action_result import FileActionResult


def _fake_file_descriptor() -> AdapterDescriptor:
    return external_adapter_descriptor(
        adapter_id="fake.file_action_adapter",
        adapter_kind="fake_file",
        adapter_name="Fake File Action Adapter",
        action_kind="file_action",
        envelope_type="file_action_request",
        mode=AdapterMode.FAKE,
        side_effect_declared="none",
        resource_usage_declared="fake_usage_only",
        audit_requirement_declared="test_trace_only",
        supports_fake=True,
        test_only=True,
    )


@dataclass(frozen=True, slots=True)
class FakeFileAdapter:
    """Deterministic test adapter; it does not read or mutate files."""

    adapter_descriptor: AdapterDescriptor = field(default_factory=_fake_file_descriptor)

    def describe(self) -> AdapterDescriptor:
        return self.adapter_descriptor

    def prepare_file_action(self, request: FileActionRequest) -> FileActionResult | FileActionFailure:
        return self.fake_file_action(request)

    def fake_file_action(self, request: FileActionRequest) -> FileActionResult:
        return FileActionResult(
            result_ref=new_adapter_typed_ref("file_action_result"),
            request_ref=request.request_ref,
            output_ref=new_adapter_typed_ref("file_output"),
            evidence_ref=new_adapter_typed_ref("file_evidence"),
            side_effect_summary="fake_file_no_effect",
            resource_usage_summary="fake_usage_only",
            payload_items=(("file_result", "fake"), ("real_file_mutation", "false")),
            fake_result=True,
            real_file_read=False,
            real_file_mutation=False,
        )
