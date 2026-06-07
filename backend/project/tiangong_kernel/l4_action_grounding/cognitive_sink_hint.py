"""L4 动作结果认知回流 hint。

该对象只携带记忆、遗忘、学习、检索和隐私复核的引用，不写记忆、不执行遗忘。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class ActionResultCognitiveSinkHint:
    """动作结果认知 sink 提示。"""

    hint_ref: TypedRef
    memory_candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    forgetting_intent_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    retention_boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    learning_signal_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    retrieval_followup_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    privacy_review_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    ref_only: bool = True
    writes_memory: bool = False
    executes_forgetting: bool = False
    stores_sensitive_plaintext: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.advisory_only, "ActionResultCognitiveSinkHint.advisory_only")
        ensure_true(self.ref_only, "ActionResultCognitiveSinkHint.ref_only")
        ensure_false(self.writes_memory, "ActionResultCognitiveSinkHint.writes_memory")
        ensure_false(self.executes_forgetting, "ActionResultCognitiveSinkHint.executes_forgetting")
        ensure_false(self.stores_sensitive_plaintext, "ActionResultCognitiveSinkHint.stores_sensitive_plaintext")
        ensure_schema_version(self.schema_version, "ActionResultCognitiveSinkHint.schema_version")
