import importlib
import inspect
import pkgutil
from enum import Enum

import tiangong_kernel.l0_primitives as l0


def _l0_modules():
    for module_info in pkgutil.iter_modules(l0.__path__):
        yield importlib.import_module(f"{l0.__name__}.{module_info.name}")


def test_all_l0_enums_have_unknown_string_fallback_and_unique_values():
    checked = []
    violations = []
    for module in _l0_modules():
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if obj.__module__ != module.__name__ or not issubclass(obj, Enum):
                continue
            checked.append(f"{module.__name__}.{obj.__name__}")
            values = [item.value for item in obj]
            if "UNKNOWN" not in obj.__members__:
                violations.append((obj.__name__, "missing UNKNOWN"))
            if any(not isinstance(value, str) for value in values):
                violations.append((obj.__name__, "non-string enum value"))
            if len(values) != len(set(values)):
                violations.append((obj.__name__, "duplicate enum value"))
    assert checked
    assert violations == []
