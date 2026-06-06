from pathlib import Path


L3_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l3_orchestration"
ALLOWED_RUNTIME_TOKENS = {
    "RuntimeSliceProjectionState",
    "runtime_slice_projection",
}


def test_runtime_terms_are_only_l2_projection_state_whitelist():
    """RuntimeSliceProjectionState 是允许的 L2 状态投影引用，不是旧 Runtime 主链。"""
    violations = []
    for path in L3_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            if "Runtime" not in line and "runtime" not in line:
                continue
            normalized = line.strip()
            if any(token in normalized for token in ALLOWED_RUNTIME_TOKENS):
                continue
            violations.append((path.name, line_no, normalized))
    assert violations == []
