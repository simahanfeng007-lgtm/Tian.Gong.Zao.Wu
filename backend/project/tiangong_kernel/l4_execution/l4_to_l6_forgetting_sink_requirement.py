"""L4 到 L6 遗忘 sink 需求对象。

L4 只声明未来 L6 遗忘、删除、墓碑和隐私保留服务的需求引用，不执行遗忘。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class L4ToL6ForgettingSinkRequirement:
    """L4 到 L6 遗忘 sink 需求。"""

    requirement_ref: TypedRef
    forgetting_intent_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    retention_boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    deletion_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    tombstone_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str = ""
    requirement_only: bool = True
    implements_forgetting_system: bool = False
    executes_forgetting: bool = False
    deletes_memory: bool = False
    stores_sensitive_plaintext: bool = False
    requires_l5_boundary: bool = field(default=True)
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.summary, "L4ToL6ForgettingSinkRequirement.summary")
        ensure_true(self.requirement_only, "L4ToL6ForgettingSinkRequirement.requirement_only")
        ensure_false(self.implements_forgetting_system, "L4ToL6ForgettingSinkRequirement.implements_forgetting_system")
        ensure_false(self.executes_forgetting, "L4ToL6ForgettingSinkRequirement.executes_forgetting")
        ensure_false(self.deletes_memory, "L4ToL6ForgettingSinkRequirement.deletes_memory")
        ensure_false(self.stores_sensitive_plaintext, "L4ToL6ForgettingSinkRequirement.stores_sensitive_plaintext")
        ensure_true(self.requires_l5_boundary, "L4ToL6ForgettingSinkRequirement.requires_l5_boundary")
        ensure_schema_version(self.schema_version, "L4ToL6ForgettingSinkRequirement.schema_version")
