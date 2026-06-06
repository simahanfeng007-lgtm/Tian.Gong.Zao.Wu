from pathlib import Path


FORBIDDEN_SYMBOLS = (
    "Ability" + "Package",
    "Capability" + "Port",
    "Ability" + "Package" + "Port",
    "Skill" + "Registry",
    "Tool" + "Registry",
    "Tool" + "Group" + "Registry",
    "Model" + "Client",
    "Shell" + "Runner",
    "Desktop" + "Controller",
)


def test_l4_phase8_source_does_not_restore_legacy_or_l6_symbol_names():
    root = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l4_execution"
    source = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))

    for symbol in FORBIDDEN_SYMBOLS:
        assert symbol not in source
