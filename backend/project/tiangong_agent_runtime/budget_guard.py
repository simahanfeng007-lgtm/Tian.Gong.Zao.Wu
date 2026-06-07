"""预算守卫。"""

from __future__ import annotations


class BudgetExceeded(RuntimeError):
    pass


class StepBudgetGuard:
    def __init__(self, max_steps: int) -> None:
        self.max_steps = max_steps

    def check(self, step_count: int) -> None:
        if step_count > self.max_steps:
            raise BudgetExceeded(f"执行步骤超过上限：{self.max_steps}")
