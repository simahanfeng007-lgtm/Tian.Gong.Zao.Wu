"""L3 version migration and hot-switch advisory flow objects."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class VersionMigrationFlowAdvice:
    advice_ref: TypedRef
    migration_ref: TypedRef | None = None
    validation_ref: TypedRef | None = None
    rollback_anchor_ref: TypedRef | None = None
    replay_compatibility_ref: TypedRef | None = None
    advisory_only: bool = True
    executes_migration: bool = False
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class HotSwitchReadinessRouteRanking:
    ranking_ref: TypedRef
    candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    readiness_score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    activates_version: bool = False
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION


SwitchRollbackRouteAdvice = VersionMigrationFlowAdvice
OldEventReplayRouteAdvice = VersionMigrationFlowAdvice
BreakingChangeReviewAdvice = VersionMigrationFlowAdvice
PreSwitchValidationAdvice = VersionMigrationFlowAdvice
PostSwitchObservationAdvice = VersionMigrationFlowAdvice
