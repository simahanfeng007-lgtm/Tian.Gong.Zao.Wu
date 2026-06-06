"""No live action guarantee for L4 phase 8 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_ACTION_SURFACES, L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_text_items, ensure_true


@dataclass(frozen=True, slots=True)
class L4NoLiveActionGuarantee:
    """Guarantee that L4 closure enables no live action surface."""

    guarantee_ref: TypedRef
    covered_surfaces: tuple[str, ...] = field(default_factory=lambda: L4_ACTION_SURFACES)
    guarantee_only: bool = True
    enables_live_action: bool = False
    calls_model: bool = False
    invokes_tool: bool = False
    writes_file: bool = False
    accesses_network: bool = False
    executes_shell: bool = False
    controls_desktop: bool = False
    commits_transaction: bool = False
    allocates_resource: bool = False
    schedules_concurrency: bool = False
    executes_replay: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_text_items(self.covered_surfaces, "L4NoLiveActionGuarantee.covered_surfaces", 128)
        ensure_true(self.guarantee_only, "L4NoLiveActionGuarantee.guarantee_only")
        ensure_false(self.enables_live_action, "L4NoLiveActionGuarantee.enables_live_action")
        ensure_false(self.calls_model, "L4NoLiveActionGuarantee.calls_model")
        ensure_false(self.invokes_tool, "L4NoLiveActionGuarantee.invokes_tool")
        ensure_false(self.writes_file, "L4NoLiveActionGuarantee.writes_file")
        ensure_false(self.accesses_network, "L4NoLiveActionGuarantee.accesses_network")
        ensure_false(self.executes_shell, "L4NoLiveActionGuarantee.executes_shell")
        ensure_false(self.controls_desktop, "L4NoLiveActionGuarantee.controls_desktop")
        ensure_false(self.commits_transaction, "L4NoLiveActionGuarantee.commits_transaction")
        ensure_false(self.allocates_resource, "L4NoLiveActionGuarantee.allocates_resource")
        ensure_false(self.schedules_concurrency, "L4NoLiveActionGuarantee.schedules_concurrency")
        ensure_false(self.executes_replay, "L4NoLiveActionGuarantee.executes_replay")
        ensure_schema_version(self.schema_version, "L4NoLiveActionGuarantee.schema_version")
