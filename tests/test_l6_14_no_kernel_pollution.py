from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "tiangong_kernel"


def test_kernel_does_not_import_l614_planner_or_outer_layers() -> None:
    forbidden_terms = [
        "tiangong_agent_runtime",
        "tiangong_agent_shell",
        "ModelPlanner",
        "PlannerMode",
        "TIANGONG_PLANNER_MODE",
        "planner_mode",
        "run_agent.py",
    ]
    offenders: list[str] = []
    for path in KERNEL.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for term in forbidden_terms:
            if term in text:
                offenders.append(f"{path.relative_to(ROOT)}::{term}")
    assert offenders == []
