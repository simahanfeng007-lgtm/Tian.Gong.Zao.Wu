"""L4 第二阶段边界失败对象。"""

from __future__ import annotations

from dataclasses import dataclass

from .permit_failure import PermitFailure, PermitFailureKind


@dataclass(frozen=True, slots=True)
class BoundaryMissingFailure(PermitFailure):
    failure_kind: PermitFailureKind = PermitFailureKind.PERMIT_MISSING
    reason_summary: str = "boundary decision ref is missing"


@dataclass(frozen=True, slots=True)
class BoundaryDeniedFailure(PermitFailure):
    failure_kind: PermitFailureKind = PermitFailureKind.PERMIT_DENIED
    reason_summary: str = "boundary decision ref explicitly denies grounding"


@dataclass(frozen=True, slots=True)
class BoundaryExpiredFailure(PermitFailure):
    failure_kind: PermitFailureKind = PermitFailureKind.PERMIT_EXPIRED
    reason_summary: str = "boundary decision ref is expired"


@dataclass(frozen=True, slots=True)
class BoundaryScopeMismatchFailure(PermitFailure):
    failure_kind: PermitFailureKind = PermitFailureKind.PERMIT_SCOPE_MISMATCH
    reason_summary: str = "boundary decision scope does not structurally cover requested scope"
