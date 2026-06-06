from dataclasses import FrozenInstanceError, is_dataclass

import pytest

import tiangong_kernel.l4_action_grounding as l4
from l4_phase1_builders import build_l4_phase1_objects


def test_l4_phase1_package_imports_and_exports_basic_objects():
    assert l4.L4_ACTION_GROUNDING_SCHEMA_VERSION == "0.1"
    assert "ActionGroundingIdentity" in l4.__all__
    assert "FakeActionGroundingRunner" in l4.__all__
    objects = build_l4_phase1_objects()
    for name in (
        "identity",
        "status",
        "intake",
        "context",
        "session",
        "step",
        "result",
        "failure",
        "error",
        "disabled",
        "projection",
        "summary",
        "invariant",
        "permit_invariant",
        "no_live_invariant",
        "no_auto_invariant",
    ):
        item = objects[name]
        assert is_dataclass(item)
        assert hasattr(type(item), "__slots__")


def test_l4_phase1_objects_are_frozen_and_do_not_enable_live_action():
    objects = build_l4_phase1_objects()
    with pytest.raises(FrozenInstanceError):
        objects["status"].ready_for_live_action = True
    assert objects["status"].ready_for_live_action is False
    assert objects["context"].live_action_enabled is False
    assert objects["step"].live_action_enabled is False
    assert objects["session"].l4_autonomous is False
