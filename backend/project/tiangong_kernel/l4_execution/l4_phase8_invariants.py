"""Phase 8 invariants for L4 closure."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class L4Phase8Invariant:
    invariant_ref: TypedRef
    invariant_name: str
    invariant_only: bool = True
    l4_can_override: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.invariant_name, "L4Phase8Invariant.invariant_name", 128)
        ensure_true(self.invariant_only, "L4Phase8Invariant.invariant_only")
        ensure_false(self.l4_can_override, "L4Phase8Invariant.l4_can_override")
        ensure_schema_version(self.schema_version, "L4Phase8Invariant.schema_version")


@dataclass(frozen=True, slots=True)
class NoDirectL5L6ProgressionInvariant(L4Phase8Invariant):
    invariant_name: str = "NoDirectL5L6ProgressionInvariant"


@dataclass(frozen=True, slots=True)
class NoSkipL4QualityGateInvariant(L4Phase8Invariant):
    invariant_name: str = "NoSkipL4QualityGateInvariant"


@dataclass(frozen=True, slots=True)
class NoPhase8LiveActionInvariant(L4Phase8Invariant):
    invariant_name: str = "NoPhase8LiveActionInvariant"
