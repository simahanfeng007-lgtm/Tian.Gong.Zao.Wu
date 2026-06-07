"""L2 记忆遗忘治理状态。

本模块只表达 retention、decay、interference、suppression、pruning、revision、
deletion、tombstone、privacy 和 audit/evidence 的引用链，不执行遗忘或删除。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


def _unit(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _short(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _true(value: bool, field_name: str) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must remain true")


def _false(value: bool, field_name: str) -> None:
    if value is not False:
        raise ValueError(f"{field_name} must remain false")


@dataclass(frozen=True, slots=True)
class MemoryForgettingStateBase:
    """记忆遗忘治理基础状态，只保存引用和审查事实。"""

    identity: L2StateIdentity
    status: L2StateStatus
    memory_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    forgetting_ref: TypedRef | None = None
    retention_ref: TypedRef | None = None
    deletion_ref: TypedRef | None = None
    tombstone_ref: TypedRef | None = None
    privacy_ref: TypedRef | None = None
    retention_policy_ref: TypedRef | None = None
    consent_ref: TypedRef | None = None
    audit_ref: TypedRef | None = None
    evidence_ref: TypedRef | None = None
    boundary_status: L2StateBoundary | None = None
    summary: str = ""
    state_only: bool = True
    ref_only: bool = True
    no_memory_read: bool = True
    no_context_write: bool = True
    executes_forgetting: bool = False
    deletes_memory: bool = False
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _short(self.summary, f"{self.__class__.__name__}.summary")
        _true(self.state_only, f"{self.__class__.__name__}.state_only")
        _true(self.ref_only, f"{self.__class__.__name__}.ref_only")
        _true(self.no_memory_read, f"{self.__class__.__name__}.no_memory_read")
        _true(self.no_context_write, f"{self.__class__.__name__}.no_context_write")
        _false(self.executes_forgetting, f"{self.__class__.__name__}.executes_forgetting")
        _false(self.deletes_memory, f"{self.__class__.__name__}.deletes_memory")
        if not self.schema_version:
            raise ValueError(f"{self.__class__.__name__}.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MemoryGovernanceState(MemoryForgettingStateBase):
    """记忆治理总状态。"""

    governance_ref: TypedRef | None = None
    review_required: bool = True


@dataclass(frozen=True, slots=True)
class MemoryRetentionState(MemoryForgettingStateBase):
    """记忆保留状态。"""

    retention_score: float = 0.0
    retention_reason_refs: tuple[TypedRef, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        MemoryForgettingStateBase.__post_init__(self)
        _unit(self.retention_score, "MemoryRetentionState.retention_score")


@dataclass(frozen=True, slots=True)
class MemoryDecayState(MemoryForgettingStateBase):
    """记忆衰减状态。"""

    decay_score: float = 0.0
    decay_trace_ref: TypedRef | None = None

    def __post_init__(self) -> None:
        MemoryForgettingStateBase.__post_init__(self)
        _unit(self.decay_score, "MemoryDecayState.decay_score")


@dataclass(frozen=True, slots=True)
class MemoryInterferenceState(MemoryForgettingStateBase):
    """记忆干扰状态。"""

    interference_score: float = 0.0
    interfering_memory_refs: tuple[TypedRef, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        MemoryForgettingStateBase.__post_init__(self)
        _unit(self.interference_score, "MemoryInterferenceState.interference_score")


@dataclass(frozen=True, slots=True)
class MemorySuppressionState(MemoryForgettingStateBase):
    """记忆抑制状态。"""

    suppression_ref: TypedRef | None = None
    suppression_reason_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    hidden_only: bool = True

    def __post_init__(self) -> None:
        MemoryForgettingStateBase.__post_init__(self)
        _true(self.hidden_only, "MemorySuppressionState.hidden_only")


@dataclass(frozen=True, slots=True)
class MemoryPruningState(MemoryForgettingStateBase):
    """记忆剪枝状态。"""

    pruning_ref: TypedRef | None = None
    pruning_candidate_count: int = 0

    def __post_init__(self) -> None:
        MemoryForgettingStateBase.__post_init__(self)
        if self.pruning_candidate_count < 0:
            raise ValueError("MemoryPruningState.pruning_candidate_count cannot be negative")


@dataclass(frozen=True, slots=True)
class MemoryRevisionState(MemoryForgettingStateBase):
    """记忆修订状态。"""

    revision_ref: TypedRef | None = None
    superseded_memory_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    revision_requires_evidence: bool = True

    def __post_init__(self) -> None:
        MemoryForgettingStateBase.__post_init__(self)
        _true(self.revision_requires_evidence, "MemoryRevisionState.revision_requires_evidence")


@dataclass(frozen=True, slots=True)
class MemoryDeletionLinkState(MemoryForgettingStateBase):
    """遗忘、删除、墓碑、审计和证据的链路状态。"""

    deletion_ticket_ref: TypedRef | None = None
    deletion_evidence_ref: TypedRef | None = None
    physical_erasure_performed: bool = False

    def __post_init__(self) -> None:
        MemoryForgettingStateBase.__post_init__(self)
        _false(self.physical_erasure_performed, "MemoryDeletionLinkState.physical_erasure_performed")


@dataclass(frozen=True, slots=True)
class MemoryPrivacyBoundaryState(MemoryForgettingStateBase):
    """记忆隐私与保留边界状态。"""

    privacy_review_ref: TypedRef | None = None
    stores_sensitive_plaintext: bool = False
    requires_l5_boundary: bool = True

    def __post_init__(self) -> None:
        MemoryForgettingStateBase.__post_init__(self)
        _false(self.stores_sensitive_plaintext, "MemoryPrivacyBoundaryState.stores_sensitive_plaintext")
        _true(self.requires_l5_boundary, "MemoryPrivacyBoundaryState.requires_l5_boundary")
