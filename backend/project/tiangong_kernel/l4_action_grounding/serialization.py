"""L4 动作落地稳定序列化辅助。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps, to_primitive

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_schema_version, ensure_true


def action_grounding_to_primitive(value: Any) -> Any:
    return to_primitive(value)


def action_grounding_stable_json(value: Any) -> str:
    return stable_json_dumps(value)


def action_grounding_stable_hash(value: Any) -> str:
    return stable_hash(value)


@dataclass(frozen=True, slots=True)
class ActionGroundingSerialization:
    """序列化快照对象；只记录稳定哈希，不写入存储。"""

    serialization_ref: TypedRef
    target_ref: TypedRef | None = None
    stable_hash_value: str = ""
    serialization_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.serialization_only, "ActionGroundingSerialization.serialization_only")
        ensure_schema_version(self.schema_version, "ActionGroundingSerialization.schema_version")

    @classmethod
    def from_value(cls, serialization_ref: TypedRef, value: Any, target_ref: TypedRef | None = None) -> "ActionGroundingSerialization":
        return cls(serialization_ref=serialization_ref, target_ref=target_ref, stable_hash_value=stable_hash(value))
