from pathlib import Path


FORBIDDEN_TERMS = (
    "Runtime",
    "绁炴灑",
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
    ".get(",
    ".post(",
    ".request(",
    ".connect(",
    "tiangong_kernel.l5",
    "tiangong_kernel.l6",
)


PHASE5_FILE_PREFIXES = (
    "desktop_action_",
    "desktop_dry_run_adapter",
    "desktop_fake_adapter",
    "external_action_",
    "external_adapter_common",
    "external_no_op_adapter",
    "external_real_disabled_stub",
    "file_action_",
    "file_dry_run_adapter",
    "file_fake_adapter",
    "network_action_",
    "network_dry_run_adapter",
    "network_fake_adapter",
    "resource_usage_descriptor",
    "reversibility_descriptor",
    "side_effect_descriptor",
    "terminal_action_",
    "terminal_dry_run_adapter",
    "terminal_fake_adapter",
)


def test_l4_phase5_has_no_legacy_or_real_external_action_terms():
    root = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l4_action_grounding"
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in root.glob("*.py")
        if path.name.startswith(PHASE5_FILE_PREFIXES)
    )
    for term in FORBIDDEN_TERMS:
        assert term not in source
