from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_l6_12_runtime_does_not_pollute_kernel_import_direction() -> None:
    kernel_root = ROOT / "tiangong_kernel"
    forbidden = [
        "tiangong_agent_runtime",
        "tiangong_agent_shell",
        "ConfirmationTicketStore",
        "export_runtime_report",
        "argparse",
        "run_agent.py",
    ]
    hits: list[str] = []
    for path in kernel_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for marker in forbidden:
            if marker in text:
                hits.append(f"{path.relative_to(ROOT)}::{marker}")
    assert hits == []
