"""L2 数据治理、隐私、披露与撤销状态对象。"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


@dataclass(frozen=True, slots=True)
class DataGovernanceBindingState:
    """数据治理绑定状态，只保存主体、同意、目的、保留和披露边界引用。"""

    identity: L2StateIdentity
    status: L2StateStatus
    subject_ref: TypedRef | None = None
    privacy_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    security_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    consent_ref: TypedRef | None = None
    purpose_ref: TypedRef | None = None
    retention_policy_ref: TypedRef | None = None
    data_lifecycle_state_ref: TypedRef | None = None
    trust_boundary_ref: TypedRef | None = None
    disclosure_boundary_ref: TypedRef | None = None
    metadata: L2StateMetadata | None = None
    value_absent: bool = True
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.value_absent:
            raise ValueError("DataGovernanceBindingState.value_absent must remain true")


MemoryPrivacyGovernanceState = DataGovernanceBindingState
ContextPrivacyGovernanceState = DataGovernanceBindingState
CredentialRevocationState = DataGovernanceBindingState
DisclosureState = DataGovernanceBindingState
