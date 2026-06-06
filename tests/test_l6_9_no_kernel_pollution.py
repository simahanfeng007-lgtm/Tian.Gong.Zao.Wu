from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "tiangong_kernel"


def test_kernel_does_not_import_agent_shell() -> None:
    offenders: list[str] = []
    for path in KERNEL.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "tiangong_agent_shell" in text or "run_agent" in text:
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_kernel_has_no_cli_or_http_adapter_terms_from_l69() -> None:
    forbidden_terms = [
        "argparse.ArgumentParser",
        "OpenAICompatibleModelClient",
        "TIANGONG_API_KEY",
        "model_config.example",
    ]
    offenders: list[str] = []
    for path in KERNEL.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for term in forbidden_terms:
            if term in text:
                offenders.append(f"{path.relative_to(ROOT)}::{term}")
    assert offenders == []
