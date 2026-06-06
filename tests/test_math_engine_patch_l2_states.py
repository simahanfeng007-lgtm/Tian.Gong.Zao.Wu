import hashlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from pathlib import Path

import pytest

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps
from tiangong_kernel.l2_state import (
    AssessmentState,
    L2StateIdentity,
    L2StateKind,
    L2StateStatus,
    L2StateStatusKind,
    MathematicalModelState,
    ModelCalibrationState,
    ModelConfidenceState,
    ModelDriftState,
    ModelInputSnapshot,
    ModelOutputSnapshot,
    ModelParameterState,
    ModelThresholdState,
    ModelTraceState,
    ModelVersionState,
    ModelWeightState,
    ScoreState,
    math_engine_state_stable_hash,
    math_engine_state_stable_json,
)


EXPECTED_L0_TREE_HASH = "D06957DCCF3253660AC0F27980D1FBC922505F8B5CEBD897C083252F6FC8EF5F"


def typed(index: int, ref_type: str) -> TypedRef:
    return TypedRef(RefId(f"ref:{index:032x}"), ref_type)


def identity(index: int) -> L2StateIdentity:
    return L2StateIdentity(state_ref=typed(index, "l2_math_engine_state"), kind=L2StateKind.MATH)


def status() -> L2StateStatus:
    return L2StateStatus(kind=L2StateStatusKind.DECLARED)


def build_states():
    return (
        MathematicalModelState(identity(1), status(), model_name="compat_math_engine"),
        ModelParameterState(identity(2), status(), parameter_name="alpha"),
        ModelWeightState(identity(3), status(), weight_name="memory", normalized_weight=0.5),
        ModelThresholdState(identity(4), status(), threshold_name="risk", normalized_threshold=0.7),
        ModelCalibrationState(identity(5), status(), summary="profile reference only"),
        ModelVersionState(identity(6), status(), version_label="0.1"),
        ScoreState(identity(7), status(), normalized_score=0.4),
        AssessmentState(identity(8), status(), summary="advisory"),
        ModelInputSnapshot(identity(9), status(), feature_refs=(typed(91, "feature"),)),
        ModelOutputSnapshot(identity(10), status(), score_refs=(typed(101, "score"),)),
        ModelTraceState(identity(11), status(), step_refs=(typed(111, "trace_step"),)),
        ModelConfidenceState(identity(12), status(), normalized_confidence=0.8),
        ModelDriftState(identity(13), status(), drift_indicator=0.2),
    )


def test_l2_math_engine_states_are_frozen_slots_and_stable():
    for item in build_states():
        assert is_dataclass(item)
        assert hasattr(type(item), "__slots__")
        with pytest.raises(FrozenInstanceError):
            item.schema_version = "changed"
        payload = stable_json_dumps(item)
        digest = stable_hash(item)
        assert isinstance(payload, str)
        assert len(digest) == 64
        assert math_engine_state_stable_json(item) == payload
        assert math_engine_state_stable_hash(item) == digest


def test_l2_math_engine_hash_changes_when_state_fact_changes():
    score = ScoreState(identity(21), status(), normalized_score=0.4)
    changed = replace(score, normalized_score=0.6)
    assert stable_hash(score) != stable_hash(changed)


def test_l2_math_engine_state_has_no_upper_imports_or_calculation_methods():
    source = Path("tiangong_kernel/l2_state/math_engine_state.py").read_text(encoding="utf-8")
    forbidden_imports = ("tiangong_kernel.l3_", "tiangong_kernel.l4_", "tiangong_kernel.l5", "tiangong_kernel.l6")
    for token in forbidden_imports:
        assert token not in source
    forbidden_defs = ("def calculate", "def compute", "def rank", "def train", "def infer", "def detect")
    for token in forbidden_defs:
        assert token not in source


def test_l0_tree_hash_is_unchanged_for_patch_baseline():
    root = Path("tiangong_kernel/l0_primitives")
    items = []
    for item in sorted(path for path in root.rglob("*") if path.is_file() and "__pycache__" not in path.parts):
        if item.suffix == ".pyc":
            continue
        digest = hashlib.sha256(item.read_bytes()).hexdigest().upper()
        items.append(f"{item.relative_to(root).as_posix()}|{digest}")
    tree_hash = hashlib.sha256("\n".join(items).encode("utf-8")).hexdigest().upper()
    assert tree_hash == EXPECTED_L0_TREE_HASH
