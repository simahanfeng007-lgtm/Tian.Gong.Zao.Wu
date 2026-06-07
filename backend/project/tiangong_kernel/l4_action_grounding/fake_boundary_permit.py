"""L4 第二阶段 test-only fake permit 对象。"""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .boundary_ref import BoundaryDecisionRef, BoundaryDecisionStatus
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true
from .permit_expiry import PermitExpiry
from .permit_ref import ActionPermitRef, PermitActionRef, PermitIssuerRef, PermitSubjectRef
from .permit_scope import PermitScope


@dataclass(frozen=True, slots=True)
class FakeBoundaryPermitForTestOnly:
    """测试专用 fake permit；production_path=True 时必须被拒绝。"""

    permit_ref: TypedRef
    issuer_ref: TypedRef
    subject_ref: TypedRef
    action_ref: TypedRef
    scope: PermitScope
    expiry: PermitExpiry
    boundary_decision_ref: BoundaryDecisionRef | None = None
    test_only: bool = True
    production_usable: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.test_only, "FakeBoundaryPermitForTestOnly.test_only")
        ensure_false(self.production_usable, "FakeBoundaryPermitForTestOnly.production_usable")
        ensure_schema_version(self.schema_version, "FakeBoundaryPermitForTestOnly.schema_version")

    def to_action_permit_ref(self) -> ActionPermitRef:
        return ActionPermitRef(
            permit_ref=self.permit_ref,
            scope=self.scope,
            expiry=self.expiry,
            issuer_ref=PermitIssuerRef(self.issuer_ref),
            subject_ref=PermitSubjectRef(self.subject_ref),
            action_ref=PermitActionRef(self.action_ref),
            boundary_decision_ref=self.boundary_decision_ref,
            test_only=self.test_only,
        )


@dataclass(frozen=True, slots=True)
class FakePermitIssuerForTestOnly:
    issuer_ref: TypedRef
    test_only: bool = True
    production_issuer: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.test_only, "FakePermitIssuerForTestOnly.test_only")
        ensure_false(self.production_issuer, "FakePermitIssuerForTestOnly.production_issuer")
        ensure_schema_version(self.schema_version, "FakePermitIssuerForTestOnly.schema_version")


@dataclass(frozen=True, slots=True)
class SyntheticBoundaryDecisionForTestOnly:
    decision_ref: TypedRef
    scope: PermitScope | None = None
    decision_status: BoundaryDecisionStatus = BoundaryDecisionStatus.GRANTED
    test_only: bool = True
    production_usable: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.test_only, "SyntheticBoundaryDecisionForTestOnly.test_only")
        ensure_false(self.production_usable, "SyntheticBoundaryDecisionForTestOnly.production_usable")
        ensure_schema_version(self.schema_version, "SyntheticBoundaryDecisionForTestOnly.schema_version")

    def to_boundary_decision_ref(self) -> BoundaryDecisionRef:
        return BoundaryDecisionRef(decision_ref=self.decision_ref, decision_status=self.decision_status, scope=self.scope)
