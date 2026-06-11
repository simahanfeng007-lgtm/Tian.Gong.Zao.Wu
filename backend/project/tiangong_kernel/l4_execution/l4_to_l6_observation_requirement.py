"""L4 to L6 observation requirement for phase 8 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_pair_items, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class L4ToL6ObservationRequirement:
    """Observation requirement only; it samples no real observation."""

    observation_requirement_ref: TypedRef
    observation_ref: TypedRef | None = None
    evidence_ref: TypedRef | None = None
    observation_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    requirement_only: bool = True
    samples_real_observation: bool = False
    reads_screen: bool = False
    stores_evidence: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_pair_items(self.observation_items, "L4ToL6ObservationRequirement.observation_items")
        ensure_true(self.requirement_only, "L4ToL6ObservationRequirement.requirement_only")
        ensure_false(self.samples_real_observation, "L4ToL6ObservationRequirement.samples_real_observation")
        ensure_false(self.reads_screen, "L4ToL6ObservationRequirement.reads_screen")
        ensure_false(self.stores_evidence, "L4ToL6ObservationRequirement.stores_evidence")
        ensure_schema_version(self.schema_version, "L4ToL6ObservationRequirement.schema_version")
