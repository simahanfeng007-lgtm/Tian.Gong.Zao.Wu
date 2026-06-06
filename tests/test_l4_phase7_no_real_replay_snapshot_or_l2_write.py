from pathlib import Path


PHASE7_REPLAY_FILE_NAMES = (
    "execution_replay_summary.py",
    "execution_determinism_hint.py",
    "execution_idempotency_hint.py",
    "execution_side_effect_summary.py",
    "execution_reconciliation_advice.py",
    "execution_checkpoint_ref.py",
    "execution_snapshot_ref.py",
    "l4_to_l6_recovery_replay_requirement.py",
)


REAL_REPLAY_TRUE_PATTERNS = (
    "executes_replay: bool = True",
    "guarantees_real_replay: bool = True",
    "contains_plain_credential: bool = True",
    "stores_sensitive_plaintext: bool = True",
    "grants_replay_permission: bool = True",
    "authorizes_repeat_execution: bool = True",
    "creates_real_checkpoint: bool = True",
    "creates_real_snapshot: bool = True",
    "writes_l2_state: bool = True",
    "implements_replay_system: bool = True",
)


def test_l4_phase7_has_no_real_replay_snapshot_or_l2_write_defaults():
    root = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l4_action_grounding"
    source = "\n".join((root / name).read_text(encoding="utf-8") for name in PHASE7_REPLAY_FILE_NAMES)

    for pattern in REAL_REPLAY_TRUE_PATTERNS:
        assert pattern not in source
