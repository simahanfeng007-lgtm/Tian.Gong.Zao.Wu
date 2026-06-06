import dataclasses
import importlib
import inspect
import pkgutil

import tiangong_kernel.l0_primitives as l0


def _l0_modules():
    for module_info in pkgutil.iter_modules(l0.__path__):
        yield importlib.import_module(f"{l0.__name__}.{module_info.name}")


def test_all_l0_dataclasses_are_frozen_and_slotted():
    checked = []
    violations = []
    for module in _l0_modules():
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if obj.__module__ != module.__name__:
                continue
            if dataclasses.is_dataclass(obj):
                checked.append(f"{module.__name__}.{obj.__name__}")
                params = obj.__dataclass_params__
                if not params.frozen or not hasattr(obj, "__slots__"):
                    violations.append(f"{module.__name__}.{obj.__name__}")
    assert checked
    assert violations == []


def test_l0_dataclass_instances_are_immutable():
    from dataclasses import FrozenInstanceError
    from tiangong_kernel.l0_primitives import Timestamp

    item = Timestamp(1)
    try:
        item.epoch_ms = 2
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("Timestamp allowed mutation")
