"""L1 版本迁移、回滚与热切换端口声明。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.trace import TraceContext

from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class VersionSwitchIntent:
    """版本切换意图，承载源版本、目标版本、迁移和回滚锚点引用。"""

    intent_ref: TypedRef
    source_version_ref: TypedRef | None = None
    target_version_ref: TypedRef | None = None
    migration_ref: TypedRef | None = None
    rollback_anchor_ref: TypedRef | None = None
    replay_compatibility_ref: TypedRef | None = None
    schema_version: str = "0.1"


ActiveVersionSlot = VersionSwitchIntent
HotSwitchBoundary = VersionSwitchIntent
SwitchReadinessCheck = VersionSwitchIntent
SwitchRollbackPlan = VersionSwitchIntent
OldEventReplayCompatibility = VersionSwitchIntent
BreakingChangeDetection = VersionSwitchIntent
MigrationPlanBoundary = VersionSwitchIntent


class VersionSwitchIntentPort(ABC):
    """版本切换意图端口，只声明切换契约。"""

    @abstractmethod
    def declare_version_switch_intent(self, intent: VersionSwitchIntent, trace: TraceContext) -> PortResult[VersionSwitchIntent]:
        raise NotImplementedError


class ActiveVersionSlotPort(ABC):
    """活跃版本槽端口，只声明当前版本槽引用。"""

    @abstractmethod
    def declare_active_version_slot(self, slot: ActiveVersionSlot, trace: TraceContext) -> PortResult[ActiveVersionSlot]:
        raise NotImplementedError


class HotSwitchBoundaryPort(ABC):
    """热切换边界端口，只声明切换边界。"""

    @abstractmethod
    def declare_hot_switch_boundary(self, boundary: HotSwitchBoundary, trace: TraceContext) -> PortResult[HotSwitchBoundary]:
        raise NotImplementedError


class SwitchReadinessCheckPort(ABC):
    """切换就绪检查端口，只声明检查引用。"""

    @abstractmethod
    def declare_switch_readiness_check(self, check: SwitchReadinessCheck, trace: TraceContext) -> PortResult[SwitchReadinessCheck]:
        raise NotImplementedError


class SwitchRollbackPlanPort(ABC):
    """切换回滚计划端口，只声明回滚计划引用。"""

    @abstractmethod
    def declare_switch_rollback_plan(self, plan: SwitchRollbackPlan, trace: TraceContext) -> PortResult[SwitchRollbackPlan]:
        raise NotImplementedError


class OldEventReplayCompatibilityPort(ABC):
    """旧事件重放兼容端口，只声明兼容性引用。"""

    @abstractmethod
    def declare_old_event_replay_compatibility(self, check: OldEventReplayCompatibility, trace: TraceContext) -> PortResult[OldEventReplayCompatibility]:
        raise NotImplementedError


class BreakingChangeDetectionPort(ABC):
    """破坏性变更检测端口，只声明检测引用。"""

    @abstractmethod
    def declare_breaking_change_detection(self, detection: BreakingChangeDetection, trace: TraceContext) -> PortResult[BreakingChangeDetection]:
        raise NotImplementedError


class MigrationPlanBoundaryPort(ABC):
    """迁移计划边界端口，只声明迁移边界引用。"""

    @abstractmethod
    def declare_migration_plan_boundary(self, boundary: MigrationPlanBoundary, trace: TraceContext) -> PortResult[MigrationPlanBoundary]:
        raise NotImplementedError
