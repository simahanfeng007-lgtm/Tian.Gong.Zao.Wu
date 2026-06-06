from pathlib import Path


FORBIDDEN_TERMS = (
    "Runtime",
    "神枢",
    "AbilityPackage",
    "CapabilityPort",
    "AbilityPackagePort",
    "call_model",
    "call_tool",
    "invoke_tool",
    "subprocess",
    "socket",
    "requests",
    "urllib",
    "httpx",
    "open(",
    "write_text",
    "write_bytes",
)


def test_l4_phase4_has_no_legacy_runtime_or_real_action_terms():
    root = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l4_action_grounding"
    source = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    for term in FORBIDDEN_TERMS:
        assert term not in source
