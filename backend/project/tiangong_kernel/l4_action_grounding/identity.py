"""L4 动作落地层身份对象。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef


L4_ACTION_GROUNDING_SCHEMA_VERSION = "0.1"


class ActionGroundingObjectKind(str, Enum):
    """L4 动作落地对象类别。"""

    UNKNOWN = "unknown"
    IDENTITY = "identity"
    STATUS = "status"
    REQUEST_INTAKE = "request_intake"
    CONTEXT = "context"
    SESSION = "session"
    STEP = "step"
    RESULT = "result"
    FAILURE = "failure"
    ERROR = "error"
    INVARIANT = "invariant"
    PROJECTION = "projection"
    RUNNER = "runner"
    ADAPTER = "adapter"
    ADAPTER_REGISTRY = "adapter_registry"
    ADAPTER_SELECTION = "adapter_selection"


def ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def ensure_true(value: bool, field_name: str) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must remain true")


def ensure_false(value: bool, field_name: str) -> None:
    if value is not False:
        raise ValueError(f"{field_name} must remain false in L4 phase 1")


def ensure_schema_version(value: str, field_name: str = "schema_version") -> None:
    if not value:
        raise ValueError(f"{field_name} cannot be empty")


@dataclass(frozen=True, slots=True)
class ActionGroundingIdentity:
    """动作落地对象身份；不注册对象、不生成真实执行主体。"""

    action_grounding_ref: TypedRef
    object_kind: ActionGroundingObjectKind = ActionGroundingObjectKind.UNKNOWN
    source_request_ref: TypedRef | None = None
    source_layer_hint: str = "l3_orchestration"
    l4_role_hint: str = "llm_action_grounding_carrier"
    source_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.source_layer_hint, "ActionGroundingIdentity.source_layer_hint", 128)
        ensure_short_text(self.l4_role_hint, "ActionGroundingIdentity.l4_role_hint", 128)
        ensure_schema_version(self.schema_version, "ActionGroundingIdentity.schema_version")
