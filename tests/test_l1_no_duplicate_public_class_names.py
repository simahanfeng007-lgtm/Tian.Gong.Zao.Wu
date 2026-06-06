"""L1 源码模块顶层公开类名唯一性测试。"""

import ast
from pathlib import Path


L1_PORTS_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l1_ports"


def _top_level_public_class_names(module_path: Path) -> list[str]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            names.append(node.name)
    return names


def test_l1_modules_do_not_define_duplicate_top_level_public_class_names():
    """同一 L1 模块内不得重复定义公开类，避免后定义覆盖前定义。"""
    duplicate_by_module: dict[str, list[str]] = {}
    for module_path in sorted(L1_PORTS_DIR.glob("*.py")):
        names = _top_level_public_class_names(module_path)
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            duplicate_by_module[module_path.name] = duplicates

    assert duplicate_by_module == {}
