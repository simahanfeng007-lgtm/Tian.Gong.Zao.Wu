import pytest

from l4_phase7_builders import concurrency_scope, isolation_context, lock_ref, phase7_ref
from tiangong_kernel.l4_action_grounding import ConcurrencyScope, ExecutionIsolationContext, ExecutionLockRef


def test_l4_phase7_concurrency_isolation_and_lock_are_descriptors_only():
    concurrency = concurrency_scope()
    isolation = isolation_context()
    lock = lock_ref()

    assert concurrency.descriptor_only is True
    assert concurrency.starts_concurrency is False
    assert concurrency.schedules_threads is False
    assert concurrency.schedules_processes is False
    assert concurrency.grants_concurrency_permission is False
    assert isolation.context_only is True
    assert isolation.creates_real_sandbox is False
    assert isolation.switches_real_user is False
    assert isolation.changes_system_permission is False
    assert isolation.starts_process is False
    assert lock.ref_only is True
    assert lock.creates_real_lock is False
    assert lock.locks_real_file is False
    assert lock.locks_database is False
    assert lock.blocks_real_thread is False


def test_l4_phase7_concurrency_isolation_and_lock_reject_real_flags():
    with pytest.raises(ValueError):
        ConcurrencyScope(concurrency_scope_ref=phase7_ref(130, "concurrency_scope"), starts_concurrency=True)
    with pytest.raises(ValueError):
        ExecutionIsolationContext(
            isolation_context_ref=phase7_ref(131, "execution_isolation_context"),
            creates_real_sandbox=True,
        )
    with pytest.raises(ValueError):
        ExecutionLockRef(lock_ref=phase7_ref(132, "execution_lock"), creates_real_lock=True)
