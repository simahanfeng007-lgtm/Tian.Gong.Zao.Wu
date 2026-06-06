"""Adapter selection request and result objects."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .adapter_descriptor import AdapterDescriptor
from .adapter_envelope import AdapterInputEnvelope
from .adapter_failure import AdapterFailure
from .adapter_mode import AdapterMode
from .gate_result import ActionGroundingGateResult
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class AdapterSelectionRequest:
    """Selection input; selector uses this for structural matching only."""

    selection_ref: TypedRef
    input_envelope: AdapterInputEnvelope
    requested_mode: AdapterMode
    requested_adapter_id: str = ""
    requested_adapter_kind: str = ""
    gate_result: ActionGroundingGateResult | None = None
    production_path: bool = False
    allow_fake: bool = False
    allow_in_memory: bool = False
    allow_dry_run: bool = False
    allow_no_op: bool = True
    allow_real_stub_selection: bool = False
    structure_only: bool = True
    l4_grants_permission: bool = False
    l4_scores_risk: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.requested_adapter_id, "AdapterSelectionRequest.requested_adapter_id", 128)
        ensure_short_text(self.requested_adapter_kind, "AdapterSelectionRequest.requested_adapter_kind", 128)
        ensure_true(self.structure_only, "AdapterSelectionRequest.structure_only")
        ensure_false(self.l4_grants_permission, "AdapterSelectionRequest.l4_grants_permission")
        ensure_false(self.l4_scores_risk, "AdapterSelectionRequest.l4_scores_risk")
        ensure_schema_version(self.schema_version, "AdapterSelectionRequest.schema_version")


@dataclass(frozen=True, slots=True)
class AdapterSelectionResult:
    """Selection result; selecting an adapter is not authorization."""

    selection_result_ref: TypedRef
    request_ref: TypedRef
    selected_adapter_id: str = ""
    selected_adapter_kind: str = ""
    selected_mode: AdapterMode = AdapterMode.NO_OP
    selected_descriptor: AdapterDescriptor | None = None
    gate_result_ref: TypedRef | None = None
    failure: AdapterFailure | None = None
    structure_selected: bool = False
    l4_authorized_action: bool = False
    real_action_enabled: bool = False
    result_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.selected_adapter_id, "AdapterSelectionResult.selected_adapter_id", 128)
        ensure_short_text(self.selected_adapter_kind, "AdapterSelectionResult.selected_adapter_kind", 128)
        ensure_false(self.l4_authorized_action, "AdapterSelectionResult.l4_authorized_action")
        ensure_false(self.real_action_enabled, "AdapterSelectionResult.real_action_enabled")
        ensure_true(self.result_only, "AdapterSelectionResult.result_only")
        ensure_schema_version(self.schema_version, "AdapterSelectionResult.schema_version")
