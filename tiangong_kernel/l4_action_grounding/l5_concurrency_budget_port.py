"""Placeholder L5 concurrency budget port for L4 phase 7."""

from __future__ import annotations

from typing import Protocol

from .concurrency_scope import ConcurrencyScope
from .boundary_feedback_ref import BoundaryFeedbackRef


class L5ConcurrencyBudgetPort(Protocol):
    """Protocol placeholder only; L4 implements no concurrency policy."""

    def describe_concurrency_scope(self, scope: ConcurrencyScope) -> BoundaryFeedbackRef:
        ...
