"""L2 恢复状态对象，只记录恢复点、回退提示、恢复准备、恢复结果引用和连续性事实。

作用：为候选、变更、迭代、进化和实验留下可恢复状态引用，使后续层可审计恢复边界。
边界：不执行回退，不恢复文件，不读取快照，不修改状态库，不启动恢复流程。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class RecoveryAnchorKind(str, Enum):
    """恢复锚点类型枚举。

    作用：表达恢复锚点来自状态快照、检查点、版本引用、变更前引用、实验前引用或人工说明。
    边界：不读取快照，不创建检查点，不恢复版本。
    """

    UNKNOWN = "unknown"
    STATE_SNAPSHOT = "state_snapshot"
    CHECKPOINT = "checkpoint"
    VERSION_REF = "version_ref"
    BEFORE_CHANGE_REF = "before_change_ref"
    BEFORE_EXPERIMENT_REF = "before_experiment_ref"
    HUMAN_NOTE_REF = "human_note_ref"


class RecoveryReadinessStatus(str, Enum):
    """恢复准备状态枚举。

    作用：表达恢复准备未知、已声明、缺少锚点、缺少验证、缺少边界、准备就绪、阻断或移交。
    边界：不执行恢复，不创建锚点，不运行验证。
    """

    UNKNOWN = "unknown"
    DECLARED = "declared"
    ANCHOR_MISSING = "anchor_missing"
    VALIDATION_MISSING = "validation_missing"
    BOUNDARY_MISSING = "boundary_missing"
    READY = "ready"
    BLOCKED = "blocked"
    HANDED_OFF = "handed_off"


class RecoveryOutcomeStatus(str, Enum):
    """恢复结果引用状态枚举。

    作用：表达恢复结果未知、未引用、已引用、部分引用、冲突、过期或阻断。
    边界：不计算恢复结果，不判定恢复成功，不改写状态。
    """

    UNKNOWN = "unknown"
    NOT_REFERENCED = "not_referenced"
    REFERENCED = "referenced"
    PARTIAL = "partial"
    CONFLICTED = "conflicted"
    EXPIRED = "expired"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class RecoveryAnchorState:
    """恢复锚点状态对象。

    作用：记录恢复锚点引用、锚点类型、目标引用、快照引用、版本引用和摘要。
    边界：不读取快照，不复制版本，不生成恢复点。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    recovery_anchor_ref: TypedRef | None = None
    anchor_kind: RecoveryAnchorKind = RecoveryAnchorKind.UNKNOWN
    target_ref: TypedRef | None = None
    snapshot_ref: TypedRef | None = None
    version_ref: TypedRef | None = None
    summary: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.summary) > 512:
            raise ValueError("RecoveryAnchorState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("RecoveryAnchorState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RollbackHintState:
    """回退提示状态对象。

    作用：记录回退提示引用、目标引用、恢复锚点、原因、边界和证据引用。
    边界：不执行回退，不修改文件，不恢复状态，不撤销候选。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    rollback_hint_ref: TypedRef | None = None
    target_ref: TypedRef | None = None
    recovery_anchor_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_status: L2StateBoundary | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.reason_summary) > 512:
            raise ValueError("RollbackHintState.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("RollbackHintState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoveryReadinessState:
    """恢复准备状态对象。

    作用：记录恢复目标、锚点、验证引用、边界引用、准备状态和缺失摘要。
    边界：不运行验证，不读取锚点，不执行恢复。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    recovery_readiness_ref: TypedRef | None = None
    target_ref: TypedRef | None = None
    recovery_anchor_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    readiness_status: RecoveryReadinessStatus = RecoveryReadinessStatus.UNKNOWN
    missing_summary: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.missing_summary) > 512:
            raise ValueError("RecoveryReadinessState.missing_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("RecoveryReadinessState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoveryOutcomeRefState:
    """恢复结果引用状态对象。

    作用：记录恢复结果引用、回退提示、恢复验证、结果引用状态和摘要。
    边界：不执行恢复，不判定恢复成功，不改写状态。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    recovery_outcome_ref: TypedRef | None = None
    rollback_hint_ref: TypedRef | None = None
    recovery_validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    outcome_status: RecoveryOutcomeStatus = RecoveryOutcomeStatus.UNKNOWN
    outcome_summary: str = ""
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.outcome_summary) > 512:
            raise ValueError("RecoveryOutcomeRefState.outcome_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("RecoveryOutcomeRefState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoveryLinkState:
    """恢复链路状态对象。

    作用：记录候选、变更、实验、迭代或进化对象与恢复锚点、回退提示之间的引用关系。
    边界：不建立真实链路执行器，不调度恢复，不改写关联对象。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    recovery_link_ref: TypedRef | None = None
    source_state_ref: TypedRef | None = None
    recovery_anchor_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    rollback_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    recovery_validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    continuity_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.reason_summary) > 512:
            raise ValueError("RecoveryLinkState.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("RecoveryLinkState.schema_version cannot be empty")
