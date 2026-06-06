from dataclasses import MISSING, FrozenInstanceError, fields, is_dataclass
from enum import Enum
import inspect
import pytest
from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps

_COUNTER = 0

def rid(prefix: str = "ref") -> RefId:
    global _COUNTER
    _COUNTER += 1
    return RefId(f"{prefix}:" + f"{_COUNTER:032x}"[-32:])

def make_instance(cls):
    kwargs = {}
    for f in fields(cls):
        if f.default is not MISSING or f.default_factory is not MISSING:
            continue
        if f.name == "value" or f.name.endswith("_id"):
            kwargs[f.name] = rid()
        elif f.name in {"algorithm"}:
            kwargs[f.name] = "sha256"
        elif f.name in {"namespace", "name", "local_name"}:
            kwargs[f.name] = f.name
        elif f.name in {"major", "minor", "patch", "count"}:
            kwargs[f.name] = 0
        elif f.name == "digest":
            kwargs[f.name] = "00"
        elif f.name == "passed":
            kwargs[f.name] = True
        else:
            kwargs[f.name] = None
    return cls(**kwargs)

def assert_module_dataclasses(module):
    seen = []
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if obj.__module__ != module.__name__ or not is_dataclass(obj):
            continue
        item = make_instance(obj)
        seen.append(obj.__name__)
        with pytest.raises(FrozenInstanceError):
            item.schema_version = "x"
        assert stable_json_dumps(item) == stable_json_dumps(item)
        assert stable_hash(item) == stable_hash(item)
    assert seen

def assert_enum_values(enum_cls, expected):
    assert issubclass(enum_cls, Enum)
    for key, value in expected.items():
        assert enum_cls[key].value == value
    assert enum_cls.UNKNOWN.value == "unknown"
