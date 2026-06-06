from dataclasses import FrozenInstanceError, is_dataclass
from enum import Enum
import ast
import inspect
import re
from pathlib import Path

import pytest

import tiangong_kernel.l2_state.audit_observation_state as audit_observation_state
import tiangong_kernel.l2_state.event_stream_state as event_stream_state
import tiangong_kernel.l2_state.observation_channel_state as observation_channel_state
import tiangong_kernel.l2_state.observation_frame_state as observation_frame_state
import tiangong_kernel.l2_state.observation_metric_state as observation_metric_state
import tiangong_kernel.l2_state.observation_projection_state as observation_projection_state
import tiangong_kernel.l2_state.observation_quality_state as observation_quality_state
import tiangong_kernel.l2_state.observation_source_state as observation_source_state
from tests.test_l2_phase5_cross_phase_references import build_phase5_chain


MODULES = (
    observation_source_state,
    observation_channel_state,
    observation_frame_state,
    event_stream_state,
    observation_metric_state,
    audit_observation_state,
    observation_quality_state,
    observation_projection_state,
)
L2_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l2_state"
PHASE5_FILES = {
    "observation_source_state.py",
    "observation_channel_state.py",
    "observation_frame_state.py",
    "event_stream_state.py",
    "observation_metric_state.py",
    "audit_observation_state.py",
    "observation_quality_state.py",
    "observation_projection_state.py",
}
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")


def _public_local_classes(module):
    for _, value in inspect.getmembers(module, inspect.isclass):
        if value.__module__ == module.__name__ and not value.__name__.startswith("_"):
            yield value


def test_l2_phase5_package_and_modules_importable():
    import tiangong_kernel.l2_state as l2_state

    assert observation_source_state.ObservationSourceState
    assert observation_channel_state.ObservationChannelState
    assert observation_frame_state.ObservationFrameState
    assert event_stream_state.EventStreamState
    assert observation_metric_state.ObservationMetricState
    assert audit_observation_state.AuditObservationState
    assert observation_quality_state.ObservationQualityState
    assert observation_projection_state.ObservationProjectionState
    assert l2_state.ObservationSourceState
    assert l2_state.ObservationProjectionState


def test_l2_phase5_public_exports_extend_previous_phase_exports():
    import tiangong_kernel.l2_state as l2_state

    previous_exports = {
        "ControlPlaneState",
        "BoundaryCheckState",
        "RiskDecisionState",
        "ResourceBudgetState",
        "EnvironmentState",
        "SecurityBoundaryState",
    }
    phase5_exports = {
        "ObservationSourceKind",
        "ObservationSourceStatus",
        "ObservationSourceState",
        "ObservationChannelKind",
        "ObservationChannelStatus",
        "ObservationChannelState",
        "ObservationFrameKind",
        "ObservationFrameStatus",
        "ObservationFrameState",
        "EventStreamKind",
        "EventStreamStatus",
        "EventStreamState",
        "ObservationMetricKind",
        "ObservationMetricStatus",
        "ObservationMetricState",
        "AuditObservationKind",
        "AuditObservationStatus",
        "AuditObservationState",
        "ObservationQualityDimension",
        "ObservationQualityStatus",
        "ObservationQualityState",
        "ObservationProjectionKind",
        "ObservationProjectionStatus",
        "ObservationProjectionState",
    }
    exports = set(l2_state.__all__)
    assert previous_exports <= exports
    assert phase5_exports <= exports


def test_l2_phase5_public_dataclasses_are_frozen_and_slotted():
    violations = []
    dataclasses = []
    for module in MODULES:
        for cls in _public_local_classes(module):
            if issubclass(cls, Enum):
                continue
            dataclasses.append(cls.__name__)
            if not is_dataclass(cls):
                violations.append((cls.__name__, "not_dataclass"))
                continue
            if not cls.__dataclass_params__.frozen:
                violations.append((cls.__name__, "not_frozen"))
            if "__slots__" not in cls.__dict__:
                violations.append((cls.__name__, "no_slots"))
    assert len(dataclasses) == 8
    assert violations == []


def test_l2_phase5_objects_reject_mutation():
    item = build_phase5_chain()["frame"]
    with pytest.raises(FrozenInstanceError):
        item.observed_summary = "changed"


def test_l2_phase5_modules_and_public_classes_have_chinese_state_docstrings():
    violations = []
    for path in L2_DIR.glob("*.py"):
        if path.name not in PHASE5_FILES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        module_doc = ast.get_docstring(tree)
        if not module_doc or not CHINESE_RE.search(module_doc):
            violations.append((path.name, "module", "no_chinese"))
        if not module_doc or "作用" not in module_doc or "边界" not in module_doc:
            violations.append((path.name, "module", "missing_shape"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                doc = ast.get_docstring(node)
                if not doc or not CHINESE_RE.search(doc):
                    violations.append((path.name, node.name, "no_chinese"))
                if not doc or "作用" not in doc or "边界" not in doc:
                    violations.append((path.name, node.name, "missing_shape"))
                if doc and "状态对象" not in doc and not any(base.id == "Enum" for base in node.bases if isinstance(base, ast.Name)):
                    violations.append((path.name, node.name, "not_state_object"))
    assert violations == []
