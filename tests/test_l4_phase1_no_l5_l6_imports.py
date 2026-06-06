import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
L4_PACKAGE = PROJECT_ROOT / "tiangong_kernel" / "l4_action_grounding"


def test_l4_phase1_package_does_not_import_l5_or_l6_modules():
    imported_modules = set()
    for path in sorted(L4_PACKAGE.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
    assert not any(".l5_" in module or module.startswith("tiangong_kernel.l5_") for module in imported_modules)
    assert not any(".l6_" in module or module.startswith("tiangong_kernel.l6_") for module in imported_modules)


def test_l4_phase1_package_does_not_reintroduce_old_main_chain_terms():
    forbidden_terms = (
        "Run" + "time",
        "神" + "枢",
        "Ability" + "Package",
        "Capability" + "Port",
        "Ability" + "Package" + "Port",
    )
    combined = "\n".join(path.read_text(encoding="utf-8") for path in sorted(L4_PACKAGE.glob("*.py")))
    for term in forbidden_terms:
        assert term not in combined
