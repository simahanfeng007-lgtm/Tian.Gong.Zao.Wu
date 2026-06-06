from phase8_helpers import make_instance
from tiangong_kernel.l0_primitives.serialization import stable_json_dumps
import tiangong_kernel.l0_primitives.artifact as artifact
import tiangong_kernel.l0_primitives.evidence as evidence
import tiangong_kernel.l0_primitives.audit as audit
import tiangong_kernel.l0_primitives.versioning as versioning
import tiangong_kernel.l0_primitives.namespace as namespace
import tiangong_kernel.l0_primitives.relation as relation
import tiangong_kernel.l0_primitives.retrieval as retrieval
import tiangong_kernel.l0_primitives.validation as validation
import tiangong_kernel.l0_primitives.schedule as schedule
from dataclasses import is_dataclass
import inspect


def test_phase8_objects_have_stable_json_serialization():
    for module in (artifact, evidence, audit, versioning, namespace, relation, retrieval, validation, schedule):
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ == module.__name__ and is_dataclass(cls):
                obj = make_instance(cls)
                assert stable_json_dumps(obj) == stable_json_dumps(obj)
