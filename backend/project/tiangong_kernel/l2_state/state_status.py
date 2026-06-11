"""L2 状态码对象，只表达当前状态码、原因和证据引用，不推进状态转移。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef


class L2StateStatusKind(str, Enum):
    """L2 状态码枚举；只表达当前事实，不判断下一状态。"""

    UNKNOWN = "unknown"
    DECLARED = "declared"
    VISIBLE = "visible"
    SELECTED = "selected"
    ACTIVE = "active"
    WAITING = "waiting"
    BLOCKED = "blocked"
    DEGRADED = "degraded"
    FAILED = "failed"
    COMPLETED = "completed"
    REVOKED = "revoked"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


@dataclass(frozen=True, slots=True)
class L2StateStatus:
    """L2 状态码事实。

    作用：记录状态当前所处码位、原因、起始引用和证据引用。
    边界：不执行状态转移，不判断后续行动，不改变任何状态对象。
    """

    kind: L2StateStatusKind = L2StateStatusKind.UNKNOWN
    reason: str = ""
    since_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("L2StateStatus.schema_version cannot be empty")
