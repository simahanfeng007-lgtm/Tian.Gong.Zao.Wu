"""L2 版本迁移与热切换状态对象。"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


@dataclass(frozen=True, slots=True)
class VersionSwitchStateBase:
    """版本切换状态基类，保存候选版本、检查点、回滚锚点和证据引用。"""

    identity: L2StateIdentity
    status: L2StateStatus
    version_ref: TypedRef | None = None
    candidate_ref: TypedRef | None = None
    checkpoint_ref: TypedRef | None = None
    observation_ref: TypedRef | None = None
    rollback_anchor_ref: TypedRef | None = None
    replay_compatibility_ref: TypedRef | None = None
    breaking_change_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    readiness_score: float = 0.0
    metadata: L2StateMetadata | None = None
    state_only: bool = True
    executes_switch: bool = False
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.readiness_score <= 1.0:
            raise ValueError("VersionSwitchStateBase.readiness_score must be between 0 and 1")


ActiveVersionSlotState = VersionSwitchStateBase
VersionSwitchCandidateState = VersionSwitchStateBase
MigrationPlanState = VersionSwitchStateBase
HotSwitchReadinessState = VersionSwitchStateBase
SwitchCheckpointState = VersionSwitchStateBase
PostSwitchObservationState = VersionSwitchStateBase
SwitchRollbackAnchorState = VersionSwitchStateBase
OldEventReplayCompatibilityState = VersionSwitchStateBase
BreakingChangeRiskState = VersionSwitchStateBase
