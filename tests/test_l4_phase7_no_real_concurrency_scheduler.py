from pathlib import Path


PHASE7_CONCURRENCY_FILE_NAMES = (
    "concurrency_scope.py",
    "execution_isolation_context.py",
    "execution_lock_ref.py",
)


FORBIDDEN_CONCURRENCY_TERMS = (
    "threading",
    "multiprocessing",
    "asyncio.create_task",
    "ThreadPoolExecutor",
    "ProcessPoolExecutor",
    "Lock(",
    "RLock(",
    "Semaphore(",
    "fcntl",
    "msvcrt",
)


REAL_CONCURRENCY_TRUE_PATTERNS = (
    "starts_concurrency: bool = True",
    "schedules_threads: bool = True",
    "schedules_processes: bool = True",
    "creates_real_sandbox: bool = True",
    "starts_process: bool = True",
    "creates_real_lock: bool = True",
    "locks_real_file: bool = True",
    "locks_database: bool = True",
    "blocks_real_thread: bool = True",
)


def test_l4_phase7_has_no_real_concurrency_scheduler_or_lock_code():
    root = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l4_action_grounding"
    source = "\n".join((root / name).read_text(encoding="utf-8") for name in PHASE7_CONCURRENCY_FILE_NAMES)

    for pattern in REAL_CONCURRENCY_TRUE_PATTERNS:
        assert pattern not in source
    for term in FORBIDDEN_CONCURRENCY_TERMS:
        assert term not in source
