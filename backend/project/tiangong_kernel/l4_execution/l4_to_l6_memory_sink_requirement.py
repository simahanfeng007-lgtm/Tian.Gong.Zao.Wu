"""L4 到 L6 记忆 sink 需求对象。

L4 只声明未来 L6 可能需要承接的记忆候选引用，不实现记忆系统。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class L4ToL6MemorySinkRequirement:
    """L4 到 L6 记忆 sink 需求。"""

    requirement_ref: TypedRef
    memory_candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    retrieval_followup_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    learning_signal_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    privacy_review_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str = ""
    requirement_only: bool = True
    implements_memory_system: bool = False
    writes_memory: bool = False
    stores_sensitive_plaintext: bool = False
    requires_l5_boundary: bool = field(default=True)
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.summary, "L4ToL6MemorySinkRequirement.summary")
        ensure_true(self.requirement_only, "L4ToL6MemorySinkRequirement.requirement_only")
        ensure_false(self.implements_memory_system, "L4ToL6MemorySinkRequirement.implements_memory_system")
        ensure_false(self.writes_memory, "L4ToL6MemorySinkRequirement.writes_memory")
        ensure_false(self.stores_sensitive_plaintext, "L4ToL6MemorySinkRequirement.stores_sensitive_plaintext")
        ensure_true(self.requires_l5_boundary, "L4ToL6MemorySinkRequirement.requires_l5_boundary")
        ensure_schema_version(self.schema_version, "L4ToL6MemorySinkRequirement.schema_version")
