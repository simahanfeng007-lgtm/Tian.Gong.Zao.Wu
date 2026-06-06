from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "tiangong_kernel"


def test_kernel_does_not_import_agent_runtime_shell_or_l611_suggestions() -> None:
    offenders: list[str] = []
    forbidden = [
        "tiangong_agent_runtime",
        "tiangong_agent_shell",
        "PluginSuggestionBridge",
        "LongChainRunner",
        "run_agent.py",
    ]
    for path in KERNEL.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for term in forbidden:
            if term in text:
                offenders.append(f"{path.relative_to(ROOT)}::{term}")
    assert offenders == []
