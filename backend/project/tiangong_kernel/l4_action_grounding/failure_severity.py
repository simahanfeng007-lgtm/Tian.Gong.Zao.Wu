"""Failure severity values for L4 phase 6 returns."""

from __future__ import annotations

from enum import Enum


class FailureSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    RECOVERABLE = "recoverable"
    BLOCKING = "blocking"
    CRITICAL = "critical"
