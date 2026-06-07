"""Placeholder L6 recovery service port for L4 phase 7."""

from __future__ import annotations

from typing import Protocol

from .execution_rollback_intent import ExecutionRollbackIntent
from .recovery_requirement_ref import RecoveryRequirementRef


class L6RecoveryServicePort(Protocol):
    """Protocol placeholder only; L4 performs no recovery."""

    def describe_recovery_requirement(self, requirement_ref: RecoveryRequirementRef) -> ExecutionRollbackIntent:
        ...
