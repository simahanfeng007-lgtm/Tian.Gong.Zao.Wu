import dataclasses
import importlib
import inspect
import pkgutil

import tiangong_kernel.l0_primitives as l0


def _l0_modules():
    for module_info in pkgutil.iter_modules(l0.__path__):
        yield importlib.import_module(f"{l0.__name__}.{module_info.name}")


def test_l0_ref_classes_are_dataclasses_when_local():
    ref_classes = []
    violations = []
    for module in _l0_modules():
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if obj.__module__ != module.__name__ or not name.endswith("Ref"):
                continue
            ref_classes.append(f"{module.__name__}.{name}")
            if not dataclasses.is_dataclass(obj):
                violations.append(f"{module.__name__}.{name}")
    assert ref_classes
    assert violations == []
