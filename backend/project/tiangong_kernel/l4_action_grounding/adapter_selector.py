"""Adapter selector skeleton for structural matching."""

from __future__ import annotations

from .adapter_descriptor import AdapterDescriptor
from .adapter_failure import (
    AdapterCapabilityMismatchFailure,
    AdapterFailure,
    AdapterModeMismatchFailure,
    AdapterNotFoundFailure,
    AdapterPermitRequiredFailure,
    AdapterProductionDisabledFailure,
    AdapterScopeMismatchFailure,
    AdapterTestOnlyModeFailure,
    new_adapter_typed_ref,
)
from .adapter_mode import AdapterMode
from .adapter_registry import AdapterRegistry
from .adapter_selection import AdapterSelectionRequest, AdapterSelectionResult
from .permit_validation import PermitValidationStatus


class AdapterSelector:
    """Select adapters by structure only; never grants permission."""

    def select(
        self,
        request: AdapterSelectionRequest,
        registry: AdapterRegistry,
        *,
        result_ref=None,
    ) -> AdapterSelectionResult:
        candidates = self._candidate_descriptors(request, registry)
        if not candidates:
            return self._failed(request, AdapterNotFoundFailure, "no adapter matches requested id or action kind")

        last_failure: AdapterFailure | None = None
        for descriptor in candidates:
            failure = self._check_descriptor(request, descriptor)
            if failure is None:
                return AdapterSelectionResult(
                    selection_result_ref=result_ref or new_adapter_typed_ref("adapter_selection_result"),
                    request_ref=request.selection_ref,
                    selected_adapter_id=descriptor.adapter_id,
                    selected_adapter_kind=descriptor.adapter_kind,
                    selected_mode=descriptor.mode,
                    selected_descriptor=descriptor,
                    gate_result_ref=None if request.gate_result is None else request.gate_result.gate_result_ref,
                    failure=None,
                    structure_selected=True,
                )
            last_failure = failure
        return AdapterSelectionResult(
            selection_result_ref=result_ref or new_adapter_typed_ref("adapter_selection_result"),
            request_ref=request.selection_ref,
            failure=last_failure,
            selected_mode=request.requested_mode,
            structure_selected=False,
        )

    def _candidate_descriptors(self, request: AdapterSelectionRequest, registry: AdapterRegistry) -> tuple[AdapterDescriptor, ...]:
        if request.requested_adapter_id:
            descriptor = registry.get_descriptor(request.requested_adapter_id)
            return () if descriptor is None else (descriptor,)
        descriptors = registry.descriptors_for_action(request.input_envelope.action_kind)
        if request.requested_adapter_kind:
            descriptors = tuple(item for item in descriptors if item.adapter_kind == request.requested_adapter_kind)
        descriptors = tuple(item for item in descriptors if item.mode == request.requested_mode)
        return descriptors

    def _check_descriptor(self, request: AdapterSelectionRequest, descriptor: AdapterDescriptor) -> AdapterFailure | None:
        envelope = request.input_envelope
        if descriptor.mode != request.requested_mode:
            return self._failure(request, descriptor, AdapterModeMismatchFailure, "adapter mode does not match request")
        if not self._mode_allowed(request, descriptor.mode):
            return self._failure(request, descriptor, AdapterModeMismatchFailure, "requested mode is not allowed by selection request")
        if not descriptor.structurally_supports(envelope.action_kind, envelope.envelope_type, request.requested_mode):
            return self._failure(request, descriptor, AdapterCapabilityMismatchFailure, "adapter capability does not structurally support envelope")
        if request.production_path or envelope.production_path:
            if descriptor.test_only:
                return self._failure(request, descriptor, AdapterTestOnlyModeFailure, "test-only adapter cannot enter production path")
            if not descriptor.production_enabled:
                return self._failure(request, descriptor, AdapterProductionDisabledFailure, "production path is disabled for all phase 3 adapters")
        if descriptor.requires_l5_permit:
            permit_failure = self._check_l5_structure(request, descriptor)
            if permit_failure is not None:
                return permit_failure
        if descriptor.mode == AdapterMode.REAL_STUB and not descriptor.enabled_by_default:
            return self._failure(request, descriptor, AdapterProductionDisabledFailure, "real adapter stub is disabled by default")
        return None

    def _mode_allowed(self, request: AdapterSelectionRequest, mode: AdapterMode) -> bool:
        if mode == AdapterMode.FAKE:
            return request.allow_fake
        if mode == AdapterMode.IN_MEMORY:
            return request.allow_in_memory
        if mode == AdapterMode.DRY_RUN:
            return request.allow_dry_run
        if mode == AdapterMode.NO_OP:
            return request.allow_no_op
        if mode == AdapterMode.REAL_STUB:
            return request.allow_real_stub_selection
        return False

    def _check_l5_structure(self, request: AdapterSelectionRequest, descriptor: AdapterDescriptor) -> AdapterFailure | None:
        envelope = request.input_envelope
        gate_result = request.gate_result or envelope.gate_result
        if gate_result is None or not gate_result.allowed_for_grounding or gate_result.status != PermitValidationStatus.ACCEPTED:
            return self._failure(request, descriptor, AdapterPermitRequiredFailure, "accepted L5 permit gate structure is required")
        if envelope.permit_ref is None or envelope.requested_scope is None:
            return self._failure(request, descriptor, AdapterPermitRequiredFailure, "permit ref and requested scope are required")
        if not envelope.permit_ref.scope.structurally_covers(envelope.requested_scope):
            return self._failure(request, descriptor, AdapterScopeMismatchFailure, "permit scope does not structurally cover requested scope")
        return None

    def _failed(self, request: AdapterSelectionRequest, failure_cls, message: str) -> AdapterSelectionResult:
        failure = failure_cls(
            failure_ref=new_adapter_typed_ref("adapter_failure"),
            message=message,
            action_kind=request.input_envelope.action_kind,
            mode=request.requested_mode,
        )
        return AdapterSelectionResult(
            selection_result_ref=new_adapter_typed_ref("adapter_selection_result"),
            request_ref=request.selection_ref,
            failure=failure,
            selected_mode=request.requested_mode,
            structure_selected=False,
        )

    def _failure(self, request: AdapterSelectionRequest, descriptor: AdapterDescriptor, failure_cls, message: str) -> AdapterFailure:
        return failure_cls(
            failure_ref=new_adapter_typed_ref("adapter_failure"),
            message=message,
            adapter_id=descriptor.adapter_id,
            adapter_kind=descriptor.adapter_kind,
            action_kind=request.input_envelope.action_kind,
            mode=request.requested_mode,
        )
