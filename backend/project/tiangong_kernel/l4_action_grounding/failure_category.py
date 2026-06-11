"""Failure category values for L4 phase 6 returns."""

from __future__ import annotations

from enum import Enum


class FailureCategory(str, Enum):
    VALIDATION = "validation"
    PERMIT_MISSING = "permit_missing"
    PERMIT_SCOPE_MISMATCH = "permit_scope_mismatch"
    PERMIT_EXPIRED = "permit_expired"
    ADAPTER_DISABLED = "adapter_disabled"
    ADAPTER_UNAVAILABLE = "adapter_unavailable"
    ARGUMENT_INVALID = "argument_invalid"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    EXTERNAL_ACTION_BLOCKED = "external_action_blocked"
    NORMALIZATION_FAILED = "normalization_failed"
    OBSERVATION_UNAVAILABLE = "observation_unavailable"
    UNKNOWN = "unknown"
