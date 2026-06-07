"""Placeholder L6 replay service port for L4 phase 7."""

from __future__ import annotations

from typing import Protocol

from .execution_replay_summary import ExecutionReplaySummary


class L6ReplayServicePort(Protocol):
    """Protocol placeholder only; L4 performs no replay."""

    def describe_replay_summary(self, replay_summary: ExecutionReplaySummary) -> ExecutionReplaySummary:
        ...
