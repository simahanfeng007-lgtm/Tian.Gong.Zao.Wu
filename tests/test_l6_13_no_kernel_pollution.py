from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "tiangong_kernel"


def test_l6_13_model_runtime_does_not_pollute_kernel() -> None:
    forbidden = [
        "tiangong_agent_runtime",
        "tiangong_agent_shell",
        "model_chat_adapter",
        "run_model_chat",
        "OpenAICompatibleModelClient",
        "MockModelClient",
        "argparse",
        "TIANGONG_API_KEY",
    ]
    hits: list[str] = []
    for path in KERNEL.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for marker in forbidden:
            if marker in text:
                hits.append(f"{path.relative_to(ROOT)}::{marker}")
    assert hits == []
