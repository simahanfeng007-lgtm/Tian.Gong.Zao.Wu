"""L2 世界状态对象。

世界状态只表达快照、对象引用、观察绑定、过期性和信任边界，不同步真实世界。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


def _unit(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _true(value: bool, field_name: str) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must remain true")


def _false(value: bool, field_name: str) -> None:
    if value is not False:
        raise ValueError(f"{field_name} must remain false")


@dataclass(frozen=True, slots=True)
class WorldStateBase:
    """世界状态基础对象。"""

    identity: L2StateIdentity
    status: L2StateStatus
    world_state_ref: TypedRef | None = None
    observation_ref: TypedRef | None = None
    evidence_ref: TypedRef | None = None
    trust_boundary_ref: TypedRef | None = None
    observed_at_ref: TypedRef | None = None
    stale: bool = True
    state_only: bool = True
    ref_only: bool = True
    syncs_real_world: bool = False
    canonical_without_evidence: bool = False
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _true(self.state_only, f"{self.__class__.__name__}.state_only")
        _true(self.ref_only, f"{self.__class__.__name__}.ref_only")
        _false(self.syncs_real_world, f"{self.__class__.__name__}.syncs_real_world")
        _false(self.canonical_without_evidence, f"{self.__class__.__name__}.canonical_without_evidence")
        if not self.schema_version:
            raise ValueError(f"{self.__class__.__name__}.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class WorldSnapshotState(WorldStateBase):
    """世界快照状态。"""

    snapshot_ref: TypedRef | None = None
    freshness_score: float = 0.0

    def __post_init__(self) -> None:
        WorldStateBase.__post_init__(self)
        _unit(self.freshness_score, "WorldSnapshotState.freshness_score")


@dataclass(frozen=True, slots=True)
class WorldObjectRefState(WorldStateBase):
    """世界对象引用状态。"""

    object_ref: TypedRef | None = None
    object_kind: str = "unknown"


@dataclass(frozen=True, slots=True)
class WorldObservationBindingState(WorldStateBase):
    """世界观察绑定状态。"""

    binding_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class WorldStalenessState(WorldStateBase):
    """世界状态过期性状态。"""

    staleness_status: str = "unknown"
    expired: bool = False


@dataclass(frozen=True, slots=True)
class WorldTrustBoundaryState(WorldStateBase):
    """世界状态信任边界状态。"""

    trust_score: float = 0.0

    def __post_init__(self) -> None:
        WorldStateBase.__post_init__(self)
        _unit(self.trust_score, "WorldTrustBoundaryState.trust_score")
