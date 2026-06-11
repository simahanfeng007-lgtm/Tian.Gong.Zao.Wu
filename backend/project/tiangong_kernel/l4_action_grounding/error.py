"""L4 动作落地错误分类。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_schema_version, ensure_short_text


class ActionGroundingErrorKind(str, Enum):
    STRUCTURE_INVALID = "structure_invalid"
    PERMIT_REQUIRED = "permit_required"
    DISABLED_BY_DEFAULT = "disabled_by_default"
    REAL_ACTION_FORBIDDEN = "real_action_forbidden"
    RUNNER_NOT_LIVE = "runner_not_live"
    L3_REFERENCE_MISSING = "l3_reference_missing"


@dataclass(frozen=True, slots=True)
class ActionGroundingError:
    """标准错误对象；不触发恢复、重试、审计写入或外部动作。"""

    error_ref: TypedRef | None = None
    error_kind: ActionGroundingErrorKind = ActionGroundingErrorKind.DISABLED_BY_DEFAULT
    message: str = "action grounding is disabled by default"
    detail_hint: str = ""
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.message, "ActionGroundingError.message")
        ensure_short_text(self.detail_hint, "ActionGroundingError.detail_hint")
        ensure_schema_version(self.schema_version, "ActionGroundingError.schema_version")
