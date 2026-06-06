from pathlib import Path


FORBIDDEN_IMPORT_PATTERNS = (
    "from tiangong_kernel.l5",
    "import tiangong_kernel.l5",
    "from tiangong_kernel.l6",
    "import tiangong_kernel.l6",
)


def test_l4_phase8_does_not_import_l5_or_l6_real_implementations():
    root = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l4_execution"
    source = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))

    for pattern in FORBIDDEN_IMPORT_PATTERNS:
        assert pattern not in source
