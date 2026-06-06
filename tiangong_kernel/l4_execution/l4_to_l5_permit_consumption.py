"""L4 to L5 permit consumption summary for phase 8 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_pair_items, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class L4ToL5PermitConsumptionSummary:
    """Permit consumption summary only; it never mutates real permits."""

    permit_consumption_summary_ref: TypedRef
    permit_ref: TypedRef | None = None
    action_ref: TypedRef | None = None
    consumption_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    summary_only: bool = True
    deducts_real_permit: bool = False
    renews_permit: bool = False
    issues_permit: bool = False
    extends_lease: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_pair_items(self.consumption_items, "L4ToL5PermitConsumptionSummary.consumption_items")
        ensure_true(self.summary_only, "L4ToL5PermitConsumptionSummary.summary_only")
        ensure_false(self.deducts_real_permit, "L4ToL5PermitConsumptionSummary.deducts_real_permit")
        ensure_false(self.renews_permit, "L4ToL5PermitConsumptionSummary.renews_permit")
        ensure_false(self.issues_permit, "L4ToL5PermitConsumptionSummary.issues_permit")
        ensure_false(self.extends_lease, "L4ToL5PermitConsumptionSummary.extends_lease")
        ensure_schema_version(self.schema_version, "L4ToL5PermitConsumptionSummary.schema_version")
