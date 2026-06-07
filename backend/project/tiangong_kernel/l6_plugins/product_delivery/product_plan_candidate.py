"""Product plan candidate declarations for L6 phase6."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import ProductArtifactBase, ensure_bool, ensure_ref_items


@dataclass(frozen=True)
class ProductPlanCandidate(ProductArtifactBase):
    object_ref: str = "product:l6_phase6_plan_candidate"
    stage_refs: tuple[str, ...] = field(default_factory=lambda: ("product:l6_phase6_stage_requirement", "product:l6_phase6_stage_delivery"))
    execution_plan: bool = False
    dispatches_work: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.stage_refs, "ProductPlanCandidate.stage_refs", required=True)
        ensure_bool(self.execution_plan, "ProductPlanCandidate.execution_plan")
        ensure_bool(self.dispatches_work, "ProductPlanCandidate.dispatches_work")
        if self.execution_plan or self.dispatches_work:
            raise ValueError("ProductPlanCandidate is not an execution plan and cannot dispatch work")


@dataclass(frozen=True)
class ProductMilestoneCandidate(ProductArtifactBase):
    object_ref: str = "product:l6_phase6_milestone_candidate"
    milestone_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_milestone",))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.milestone_refs, "ProductMilestoneCandidate.milestone_refs", required=True)


@dataclass(frozen=True)
class ProductTaskBreakdownCandidate(ProductArtifactBase):
    object_ref: str = "product:l6_phase6_task_breakdown_candidate"
    task_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_task_candidate",))
    runnable_now: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.task_refs, "ProductTaskBreakdownCandidate.task_refs", required=True)
        ensure_bool(self.runnable_now, "ProductTaskBreakdownCandidate.runnable_now")
        if self.runnable_now:
            raise ValueError("Task breakdown candidate is not a runnable task graph")


@dataclass(frozen=True)
class ProductDependencyGraphCandidate(ProductArtifactBase):
    object_ref: str = "product:l6_phase6_dependency_graph_candidate"
    dependency_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_dependency",))
    scheduler_state: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.dependency_refs, "ProductDependencyGraphCandidate.dependency_refs", required=True)
        ensure_bool(self.scheduler_state, "ProductDependencyGraphCandidate.scheduler_state")
        if self.scheduler_state:
            raise ValueError("Dependency graph candidate cannot become scheduler state")


@dataclass(frozen=True)
class ProductPlanRiskHint(ProductArtifactBase):
    object_ref: str = "hint:l6_phase6_product_plan_risk"
    risk_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_plan_risk",))
    direct_stop: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.risk_refs, "ProductPlanRiskHint.risk_refs", required=True)
        ensure_bool(self.direct_stop, "ProductPlanRiskHint.direct_stop")
        if self.direct_stop:
            raise ValueError("Plan risk hint should route to governance/degradation, not direct stop")


@dataclass(frozen=True)
class ProductPlanVersionCandidate(ProductArtifactBase):
    object_ref: str = "product:l6_phase6_plan_version_candidate"
    version_refs: tuple[str, ...] = field(default_factory=lambda: ("product:l6_phase6_plan_v1",))
    committed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.version_refs, "ProductPlanVersionCandidate.version_refs", required=True)
        ensure_bool(self.committed, "ProductPlanVersionCandidate.committed")
        if self.committed:
            raise ValueError("Plan version candidate cannot be committed by L6")
