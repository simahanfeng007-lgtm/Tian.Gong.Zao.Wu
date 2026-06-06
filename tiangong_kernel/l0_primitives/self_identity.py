"""自我身份事实引用原语。

本模块只定义 L0 层的自我、身份、连续性、边界、所有权与归属引用。
它只表达事实语言，不做身份判定、归属推理、认证、权限裁决、关系图计算或任何上层执行逻辑。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .identity import RefId, TypedRef


@dataclass(frozen=True, slots=True)
class SelfRef:
    """自我主体引用，表示某个系统生命体或主体的事实身份锚点。"""

    value: RefId
    label: str = ""
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("SelfRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IdentityRef:
    """身份引用，表示主体在某个身份域中的稳定事实标识，不执行认证。"""

    value: RefId
    self_ref: SelfRef | None = None
    identity_domain: str = "unknown"
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.identity_domain:
            raise ValueError("IdentityRef.identity_domain cannot be empty")
        if not self.schema_version:
            raise ValueError("IdentityRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContinuityRef:
    """连续性引用，表示身份或主体跨时间、版本、会话的事实连续关系。"""

    value: RefId
    subject_ref: TypedRef
    previous_ref: TypedRef | None = None
    continuity_kind: str = "unknown"
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.continuity_kind:
            raise ValueError("ContinuityRef.continuity_kind cannot be empty")
        if not self.schema_version:
            raise ValueError("ContinuityRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BoundaryRef:
    """身份边界引用，表示主体、身份或资源之间的事实边界，不做访问控制。"""

    value: RefId
    subject_ref: TypedRef | None = None
    boundary_kind: str = "unknown"
    related_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.boundary_kind:
            raise ValueError("BoundaryRef.boundary_kind cannot be empty")
        if not self.schema_version:
            raise ValueError("BoundaryRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OwnershipRef:
    """所有权引用，表示主体与对象之间的事实所有关系，不做授权裁决。"""

    value: RefId
    owner_ref: TypedRef
    object_ref: TypedRef
    ownership_kind: str = "unknown"
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.ownership_kind:
            raise ValueError("OwnershipRef.ownership_kind cannot be empty")
        if not self.schema_version:
            raise ValueError("OwnershipRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class AffiliationRef:
    """归属引用，表示主体与组织、范围、系统或群体之间的事实归属关系。"""

    value: RefId
    subject_ref: TypedRef
    affiliation_ref: TypedRef
    affiliation_kind: str = "unknown"
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.affiliation_kind:
            raise ValueError("AffiliationRef.affiliation_kind cannot be empty")
        if not self.schema_version:
            raise ValueError("AffiliationRef.schema_version cannot be empty")
