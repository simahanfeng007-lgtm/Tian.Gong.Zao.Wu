"""L2 连续性状态对象，只记录快照、检查点、恢复点和续接提示，不执行恢复。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.state import (
    CheckpointRef,
    ExecutionStateRef,
    RecoveryPointRef,
    RuntimeStateRef,
    StateDeltaRef,
    StateSnapshotRef,
)
from tiangong_kernel.l1_ports.state_continuity_ports import (
    CheckpointReference,
    ContinuityEvidence,
    SnapshotReference,
    StateRecoveryHint,
)

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class ContinuityKind(str, Enum):
    """连续性类别枚举。

    作用：表达连续性类别。
    边界：不保存真实上下文，不执行续跑或调度。
    """

    UNKNOWN = "unknown"
    SNAPSHOT = "snapshot"
    CHECKPOINT = "checkpoint"
    RECOVERY_POINT = "recovery_point"
    RESUME_HINT = "resume_hint"
    FAILURE_RESUME = "failure_resume"
    CONTEXT_CARRY = "context_carry"
    STATE_CHAIN = "state_chain"


class ContinuityStatus(str, Enum):
    """连续性状态枚举。

    作用：表达连续性当前状态。
    边界：不执行恢复，不回滚，不读取真实上下文。
    """

    UNKNOWN = "unknown"
    DECLARED = "declared"
    AVAILABLE = "available"
    STALE = "stale"
    BROKEN = "broken"
    BLOCKED = "blocked"
    REVOKED = "revoked"
    EXPIRED = "expired"
    RECOVERABLE = "recoverable"
    UNRECOVERABLE = "unrecoverable"


@dataclass(frozen=True, slots=True)
class ContinuityState:
    """连续性状态。

    作用：记录运行/执行状态、快照、增量、检查点、恢复点和相邻状态引用。
    边界：不创建快照，不保存检查点，不恢复状态，不读取真实上下文。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    kind: ContinuityKind = ContinuityKind.UNKNOWN
    continuity_status: ContinuityStatus = ContinuityStatus.UNKNOWN
    runtime_state_ref: RuntimeStateRef | None = None
    execution_state_ref: ExecutionStateRef | None = None
    snapshot_ref: StateSnapshotRef | None = None
    state_delta_ref: StateDeltaRef | None = None
    checkpoint_ref: CheckpointRef | None = None
    recovery_point_ref: RecoveryPointRef | None = None
    previous_state_ref: TypedRef | None = None
    next_expected_state_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    boundary: L2StateBoundary | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ContinuityState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CheckpointContinuityState:
    """检查点连续性状态。

    作用：记录检查点引用、快照引用、增量引用、L1 检查点/快照协议引用和连续性状态。
    边界：不创建快照，不保存检查点，不落盘，不执行恢复。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    checkpoint_ref: CheckpointRef | None = None
    snapshot_ref: StateSnapshotRef | None = None
    state_delta_ref: StateDeltaRef | None = None
    checkpoint_reference: SnapshotReference | CheckpointReference | None = None
    continuity: ContinuityState | None = None
    metadata: L2StateMetadata | None = None
    boundary: L2StateBoundary | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("CheckpointContinuityState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoveryContinuityState:
    """恢复连续性状态。

    作用：记录恢复点引用、失败引用、L1 恢复提示、连续性证据、可恢复状态和续接提示。
    边界：不恢复状态，不回滚，不续跑任务，不读取真实上下文。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    recovery_point_ref: RecoveryPointRef | None = None
    failure_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    recovery_hint: StateRecoveryHint | None = None
    continuity_evidence: ContinuityEvidence | None = None
    continuity: ContinuityState | None = None
    recoverable: bool | None = None
    resume_hint: str = ""
    metadata: L2StateMetadata | None = None
    boundary: L2StateBoundary | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("RecoveryContinuityState.schema_version cannot be empty")
