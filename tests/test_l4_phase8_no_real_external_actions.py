from pathlib import Path


FORBIDDEN_RUNTIME_PATTERNS = (
    "subprocess",
    "socket",
    "import requests",
    "from requests",
    "requests.",
    "urllib",
    "httpx",
    "open(",
    "write_text",
    "write_bytes",
    "Popen",
    ".get(",
    ".post(",
    ".request(",
    ".connect(",
    "threading",
    "multiprocessing",
    "ThreadPoolExecutor",
    "ProcessPoolExecutor",
    "sqlite3",
)


TRUE_OVERREACH_DEFAULTS = (
    ": bool = True",
)


ALLOWED_TRUE_DEFAULT_LINES = (
    "inventory_only: bool = True",
    "map_only: bool = True",
    "index_only: bool = True",
    "summary_only: bool = True",
    "suite_only: bool = True",
    "guarantee_only: bool = True",
    "envelope_only: bool = True",
    "feedback_only: bool = True",
    "requirement_only: bool = True",
    "need_only: bool = True",
    "report_only: bool = True",
    "checklist_only: bool = True",
    "projection_only: bool = True",
    "invariant_only: bool = True",
    "recommends_l4_quality_audit: bool = True",
)


def test_l4_phase8_has_no_runtime_action_imports_or_calls():
    root = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l4_execution"
    source = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))

    for pattern in FORBIDDEN_RUNTIME_PATTERNS:
        assert pattern not in source


def test_l4_phase8_true_defaults_are_only_closure_marker_flags():
    root = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l4_execution"
    lines = []
    for path in root.glob("*.py"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if any(pattern in line for pattern in TRUE_OVERREACH_DEFAULTS):
                lines.append(line.strip())

    for line in lines:
        assert line in ALLOWED_TRUE_DEFAULT_LINES
