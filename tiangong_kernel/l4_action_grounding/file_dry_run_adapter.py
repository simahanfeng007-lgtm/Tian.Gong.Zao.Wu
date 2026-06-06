"""Dry-run file adapter for L4 phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field

from .adapter_descriptor import AdapterDescriptor
from .adapter_failure import new_adapter_typed_ref
from .adapter_mode import AdapterMode
from .external_adapter_common import external_adapter_descriptor
from .file_action_failure import FileActionFailure
from .file_action_request import FileActionRequest
from .file_action_result import FileActionResult


def _dry_run_file_descriptor() -> AdapterDescriptor:
    return external_adapter_descriptor(
        adapter_id="dry_run.file_action_adapter",
        adapter_kind="dry_run_file",
        adapter_name="Dry Run File Action Adapter",
        action_kind="file_action",
        envelope_type="file_action_request",
        mode=AdapterMode.DRY_RUN,
        side_effect_declared="preview_only",
        resource_usage_declared="dry_run_preview_only",
        audit_requirement_declared="future_audit_requirement_ref",
        supports_dry_run=True,
    )


@dataclass(frozen=True, slots=True)
class DryRunFileAdapter:
    """Preview adapter; it does not read or mutate files."""

    adapter_descriptor: AdapterDescriptor = field(default_factory=_dry_run_file_descriptor)

    def describe(self) -> AdapterDescriptor:
        return self.adapter_descriptor

    def prepare_file_action(self, request: FileActionRequest) -> FileActionResult | FileActionFailure:
        return self.dry_run_file_action(request)

    def dry_run_file_action(self, request: FileActionRequest) -> FileActionResult:
        return FileActionResult(
            result_ref=new_adapter_typed_ref("file_action_result"),
            request_ref=request.request_ref,
            output_ref=new_adapter_typed_ref("file_dry_run_output"),
            side_effect_summary=request.side_effect.summary,
            resource_usage_summary=request.resource_usage.summary,
            payload_items=(("mode", "dry_run"), ("real_file_mutation", "false")),
            dry_run_only=True,
            real_file_read=False,
            real_file_mutation=False,
        )
