from dataclasses import is_dataclass

import tiangong_kernel.l2_state as l2_state
from l2_phase8_builders import build_all_phase8_objects
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps
from tiangong_kernel.l2_state import (
    CandidateRefState,
    L2ComponentState,
    L2FreezeState,
    L2StateCatalog,
    L2StateKind,
    ModelVisibleStateProjection,
    RunState,
    SkillSelectionState,
    ToolGroupReleaseState,
)


def test_l2_phase8_public_exports_include_first_to_eighth_phase_objects():
    required = {
        "RunState",
        "SkillSelectionState",
        "ToolGroupReleaseState",
        "CandidateRefState",
        "L2ComponentState",
        "CompatibilityGateState",
        "ModelVisibleStateProjection",
        "L2StateCatalog",
        "L2FreezeState",
    }
    assert required.issubset(set(l2_state.__all__))
    for name in required:
        assert hasattr(l2_state, name), name


def test_l2_phase8_new_state_kinds_are_available_without_removing_old_kinds():
    assert L2StateKind.RUN.value == "run"
    assert L2StateKind.CANDIDATE.value == "candidate"
    assert L2StateKind.COMPONENT.value == "component"
    assert L2StateKind.COMPATIBILITY.value == "compatibility"
    assert L2StateKind.CATALOG.value == "catalog"
    assert L2StateKind.CLOSURE.value == "closure"


def test_l2_phase8_full_l2_objects_can_share_serialization_hash_and_import_surface():
    phase8_objects = build_all_phase8_objects()
    sample_classes = (RunState, SkillSelectionState, ToolGroupReleaseState, CandidateRefState)
    for cls in sample_classes:
        assert is_dataclass(cls), cls.__name__
    for name, item in phase8_objects.items():
        assert stable_json_dumps(item), name
        assert len(stable_hash(item)) == 64, name
    assert isinstance(phase8_objects["component"], L2ComponentState)
    assert isinstance(phase8_objects["model_visible"], ModelVisibleStateProjection)
    assert isinstance(phase8_objects["state_catalog"], L2StateCatalog)
    assert isinstance(phase8_objects["freeze"], L2FreezeState)
