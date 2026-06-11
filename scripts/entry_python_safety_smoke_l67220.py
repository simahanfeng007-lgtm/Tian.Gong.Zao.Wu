from __future__ import annotations

"""Current entry Python safety smoke.

Retains the historical filename but validates the current entry-layer contract.
Checks the five residual entry-layer safeguards:
1. dependency checker really waits via input() on failure;
2. DataUp wrappers use subprocess timeouts;
3. runpy.run_path ordinary exceptions become friendly diagnostics;
4. stale TIANGONG_ROOT_HINT / invalid root hints are skipped;
5. generated launchers no longer pass through arbitrary user args.
"""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def fail(msg: str) -> None:
    raise SystemExit("FAIL: " + msg)


def assert_contains(text: str, needle: str, rel: str) -> None:
    if needle not in text:
        fail(f"{rel} missing {needle!r}")


def assert_not_contains(text: str, needle: str, rel: str) -> None:
    if needle in text:
        fail(f"{rel} contains forbidden {needle!r}")


def main() -> int:
    dep_rel = "00_ASCII_START_HERE/python/DEPENDENCY_CHECK.py"
    dep = read(dep_rel)
    assert_contains(dep, "input(", dep_rel)
    assert_contains(dep, "按回车键退出", dep_rel)
    assert_not_contains(dep, "按任意键退出", dep_rel)

    common_rel = "00_ASCII_START_HERE/python/_entry_common_l67217.py"
    common = read(common_rel)
    assert_contains(common, "timeout=timeout", common_rel)
    assert_contains(common, "subprocess.TimeoutExpired", common_rel)
    assert_contains(common, "except Exception as exc", common_rel)
    assert_contains(common, "_print_friendly_entry_error", common_rel)
    assert_contains(common, "if not path.exists():", common_rel)
    assert_contains(common, "TIANGONG_ROOT_HINT", common_rel)

    helper_rel = "desktop/dataup_update_helper_l6717.py"
    helper = read(helper_rel)
    assert_contains(helper, "timeout=timeout", helper_rel)
    assert_contains(helper, "subprocess.TimeoutExpired", helper_rel)

    for rel in [
        "scripts/launcher_templates/posix_entry.template.sh",
        "scripts/launcher_templates/mac_entry.template.command",
    ]:
        text = read(rel)
        assert_not_contains(text, '"$@"', rel)
    assert_not_contains(read("scripts/launcher_templates/windows_entry.template.bat"), "%*", "scripts/launcher_templates/windows_entry.template.bat")

    for path in ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            fail(f"syntax error in {path.relative_to(ROOT)}: {exc}")

    print("PASS entry_python_safety_smoke_l67220")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
