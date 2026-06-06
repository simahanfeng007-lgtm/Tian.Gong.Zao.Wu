from pathlib import Path


PHASE7_FILE_NAMES = (
    "execution_transaction_ref.py",
    "execution_transaction_scope.py",
    "execution_commit_intent.py",
    "execution_rollback_intent.py",
    "resource_budget_ref.py",
    "resource_usage_report.py",
    "resource_budget_consumption_summary.py",
    "resource_budget_failure.py",
    "execution_operational_summary.py",
    "transaction_resource_fake.py",
    "transaction_resource_dry_run.py",
    "transaction_resource_noop.py",
)


REAL_RESOURCE_TRUE_PATTERNS = (
    "starts_real_transaction: bool = True",
    "commits_real_transaction: bool = True",
    "rolls_back_real_transaction: bool = True",
    "executes_commit: bool = True",
    "executes_rollback: bool = True",
    "allocates_real_resource: bool = True",
    "deducts_real_quota: bool = True",
    "budget_extension_requested: bool = True",
    "reads_real_system_resource: bool = True",
    "writes_l2_state: bool = True",
    "manages_real_resource: bool = True",
)


FORBIDDEN_RUNTIME_TERMS = (
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
    "sqlite3",
)


def test_l4_phase7_has_no_real_transaction_or_resource_management_code():
    root = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l4_action_grounding"
    source = "\n".join((root / name).read_text(encoding="utf-8") for name in PHASE7_FILE_NAMES)

    for pattern in REAL_RESOURCE_TRUE_PATTERNS:
        assert pattern not in source
    for term in FORBIDDEN_RUNTIME_TERMS:
        assert term not in source
