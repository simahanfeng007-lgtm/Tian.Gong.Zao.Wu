from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "tiangong_kernel"


def test_kernel_does_not_import_agent_runtime_or_shell() -> None:
    offenders: list[str] = []
    for path in KERNEL.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "tiangong_agent_runtime" in text or "tiangong_agent_shell" in text:
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_kernel_has_no_l610_outer_layer_terms() -> None:
    forbidden_terms = [
        "from tiangong_agent_runtime",
        "import tiangong_agent_runtime",
        "RuntimeToolRegistry",
        "argparse.ArgumentParser",
        "TIANGONG_API_KEY",
        "run_agent.py",
    ]
    offenders: list[str] = []
    for path in KERNEL.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for term in forbidden_terms:
            if term in text:
                offenders.append(f"{path.relative_to(ROOT)}::{term}")
    assert offenders == []
