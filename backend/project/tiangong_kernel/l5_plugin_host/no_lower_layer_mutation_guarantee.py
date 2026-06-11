"""L5 phase 1 guarantee that lower layers are not mutated by L5 objects."""

from __future__ import annotations

from dataclasses import dataclass

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_schema_version, ensure_short_text


@dataclass(frozen=True, slots=True)
class L5NoLowerLayerMutationGuarantee:
    guarantee_ref: str
    lower_layer_mutation_present: bool = False
    direct_state_store_write_present: bool = False
    summary: str = "L5 phase 1 does not mutate L0-L4 public semantics."
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.lower_layer_mutation_present or self.direct_state_store_write_present:
            raise ValueError("L5 phase 1 must not mutate lower layers")
        ensure_short_text(self.guarantee_ref, "L5NoLowerLayerMutationGuarantee.guarantee_ref", 128)
        ensure_short_text(self.summary, "L5NoLowerLayerMutationGuarantee.summary")
        ensure_schema_version(self.schema_version, "L5NoLowerLayerMutationGuarantee.schema_version")
