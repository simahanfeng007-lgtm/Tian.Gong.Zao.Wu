"""Product handoff envelopes for L6 phase6."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import ProductArtifactBase, ensure_bool, ensure_ref_items


@dataclass(frozen=True)
class ProductHandoffEnvelope(ProductArtifactBase):
    object_ref: str = "handoff:l6_phase6_product_handoff"
    target_refs: tuple[str, ...] = field(default_factory=lambda: ("l3:orchestration_candidate", "l5:governance_review"))
    auto_merge: bool = False
    executes_handoff: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.target_refs, "ProductHandoffEnvelope.target_refs", required=True)
        ensure_bool(self.auto_merge, "ProductHandoffEnvelope.auto_merge")
        ensure_bool(self.executes_handoff, "ProductHandoffEnvelope.executes_handoff")
        if self.auto_merge or self.executes_handoff:
            raise ValueError("ProductHandoffEnvelope is not execution or auto merge")


@dataclass(frozen=True)
class ProductToL3ContinuationHint(ProductArtifactBase):
    object_ref: str = "l3:l6_phase6_product_continuation_hint"
    continuation_refs: tuple[str, ...] = field(default_factory=lambda: ("hint:l6_phase6_continue_product_task",))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.continuation_refs, "ProductToL3ContinuationHint.continuation_refs", required=True)


@dataclass(frozen=True)
class ProductToL5GovernanceHint(ProductArtifactBase):
    object_ref: str = "l5:l6_phase6_product_governance_hint"
    governance_refs: tuple[str, ...] = field(default_factory=lambda: ("review:l6_phase6_product_governance_review",))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.governance_refs, "ProductToL5GovernanceHint.governance_refs", required=True)


@dataclass(frozen=True)
class ProductToCognitiveReentryHint(ProductArtifactBase):
    object_ref: str = "handoff:l6_phase6_to_cognitive_reentry"
    reentry_refs: tuple[str, ...] = field(default_factory=lambda: ("handoff:l6_phase4_cognitive_reentry",))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.reentry_refs, "ProductToCognitiveReentryHint.reentry_refs", required=True)


@dataclass(frozen=True)
class ProductToTestingHint(ProductArtifactBase):
    object_ref: str = "test:l6_phase6_to_testing_hint"
    test_requirement_refs: tuple[str, ...] = field(default_factory=lambda: ("requirement:l6_phase6_test_run",))
    runs_tests: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.test_requirement_refs, "ProductToTestingHint.test_requirement_refs", required=True)
        ensure_bool(self.runs_tests, "ProductToTestingHint.runs_tests")
        if self.runs_tests:
            raise ValueError("ProductToTestingHint cannot run tests")


@dataclass(frozen=True)
class ProductToFutureExecutionHint(ProductArtifactBase):
    object_ref: str = "hint:l6_phase6_to_future_execution"
    future_execution_refs: tuple[str, ...] = field(default_factory=lambda: ("requirement:l6_phase6_dispatch_intent",))
    executes_now: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.future_execution_refs, "ProductToFutureExecutionHint.future_execution_refs", required=True)
        ensure_bool(self.executes_now, "ProductToFutureExecutionHint.executes_now")
        if self.executes_now:
            raise ValueError("ProductToFutureExecutionHint cannot execute now")
