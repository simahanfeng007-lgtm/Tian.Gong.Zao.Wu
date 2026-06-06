"""Recoverability hint values for L4 phase 6 returns."""

from __future__ import annotations

from enum import Enum


class FailureRecoverabilityHint(str, Enum):
    RETRY_POSSIBLE = "retry_possible"
    REPLAN_RECOMMENDED = "replan_recommended"
    RESUME_POSSIBLE = "resume_possible"
    ROLLBACK_RECOMMENDED = "rollback_recommended"
    USER_CONFIRMATION_REQUIRED = "user_confirmation_required"
    NOT_RECOVERABLE = "not_recoverable"
    UNKNOWN = "unknown"
