from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "tiangong_kernel"


def test_l6_15_context_memory_runtime_does_not_pollute_kernel_imports() -> None:
    forbidden = [
        "tiangong_agent_runtime",
        "tiangong_agent_shell",
        "ContextMemoryBridge",
        "context_memory",
        "run_agent.py",
    ]
    offenders: list[str] = []
    for path in KERNEL.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)}:{token}")
    assert offenders == []
