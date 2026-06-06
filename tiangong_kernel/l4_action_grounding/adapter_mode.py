"""Adapter mode objects for L4 action grounding.

Execution in this package means action grounding only. It does not create a
new autonomous executor or an L6 subsystem.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true


class AdapterMode(str, Enum):
    """Declared adapter mode; real_stub is a disabled shell in phase 3."""

    FAKE = "fake"
    IN_MEMORY = "in_memory"
    DRY_RUN = "dry_run"
    NO_OP = "no_op"
    REAL_STUB = "real_stub"


class AdapterExecutionMode(str, Enum):
    """Requested grounding mode, not a permission decision."""

    TEST = "test"
    SIMULATION = "simulation"
    DRY_RUN = "dry_run"
    NO_OP = "no_op"
    PRODUCTION_PATH = "production_path"


@dataclass(frozen=True, slots=True)
class AdapterModePolicy:
    """Mode policy carried by selection; it cannot enable real actions."""

    mode_policy_ref: TypedRef
    requested_mode: AdapterMode = AdapterMode.NO_OP
    execution_mode: AdapterExecutionMode = AdapterExecutionMode.NO_OP
    production_path: bool = False
    allow_fake: bool = False
    allow_in_memory: bool = False
    allow_dry_run: bool = False
    allow_no_op: bool = True
    allow_real_stub_selection: bool = False
    real_action_enabled: bool = False
    mode_policy_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_false(self.real_action_enabled, "AdapterModePolicy.real_action_enabled")
        ensure_true(self.mode_policy_only, "AdapterModePolicy.mode_policy_only")
        ensure_schema_version(self.schema_version, "AdapterModePolicy.schema_version")


ExecutionAdapterMode = AdapterExecutionMode
