from dataclasses import FrozenInstanceError, is_dataclass

import pytest

from l3_phase1_builders import build_l3_objects


def test_l3_phase1_objects_are_frozen_slots_dataclasses():
    for name, item in build_l3_objects().items():
        assert is_dataclass(item), name
        assert item.__dataclass_params__.frozen is True, name
        assert hasattr(type(item), "__slots__"), name
        with pytest.raises(FrozenInstanceError):
            item.schema_version = "x"
