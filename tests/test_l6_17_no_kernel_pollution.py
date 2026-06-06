from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_l6_17_runtime_does_not_pollute_kernel_import_direction() -> None:
    kernel_root = ROOT / "tiangong_kernel"
    forbidden = ["tiangong_agent_runtime", "tiangong_agent_shell", "diagnose_project", "repair-loop", "argparse"]
    offenders: list[str] = []
    for path in kernel_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)}::{token}")
    assert offenders == []
