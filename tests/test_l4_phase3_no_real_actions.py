from pathlib import Path

from l4_phase3_builders import envelope
from tiangong_kernel.l4_action_grounding import AdapterMode, DryRunActionAdapter, FakeActionAdapter, InMemoryActionAdapter, NoOpActionAdapter, RealActionAdapterStub


FORBIDDEN_PATTERNS = (
    "subprocess",
    "socket",
    "requests",
    "urllib",
    "httpx",
    "ToolRegistry",
    "SkillRegistry",
    "CapabilityPort",
    "AbilityPackagePort",
    "open(",
    "write_text",
    "write_bytes",
)


def test_l4_phase3_adapter_modules_do_not_import_real_action_dependencies():
    root = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l4_action_grounding"
    adapter_sources = root.glob("adapter_*.py")
    joined = "\n".join(path.read_text(encoding="utf-8") for path in adapter_sources)
    for pattern in FORBIDDEN_PATTERNS:
        assert pattern not in joined


def test_l4_phase3_adapter_invocations_report_no_real_action():
    adapters = (
        (FakeActionAdapter(), AdapterMode.FAKE),
        (InMemoryActionAdapter(), AdapterMode.IN_MEMORY),
        (DryRunActionAdapter(), AdapterMode.DRY_RUN),
        (NoOpActionAdapter(), AdapterMode.NO_OP),
        (RealActionAdapterStub(), AdapterMode.REAL_STUB),
    )
    for adapter, mode in adapters:
        result = adapter.invoke(envelope(mode=mode))
        assert result.real_action_performed is False
