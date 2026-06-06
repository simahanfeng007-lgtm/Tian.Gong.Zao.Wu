from dataclasses import fields, replace

from l2_phase9_builders import build_all_phase9_objects, build_math_objects
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps


def test_l2_phase9_all_objects_are_stably_serializable_and_hashable():
    for name, item in build_all_phase9_objects().items():
        payload = stable_json_dumps(item)
        digest = stable_hash(item)
        assert isinstance(payload, str), name
        assert len(digest) == 64, name
        assert stable_hash(item) == digest, name


def test_l2_phase9_hash_changes_when_state_fact_changes():
    score = build_math_objects()["score"]
    changed = replace(score, normalized_score=0.6)
    assert stable_hash(score) != stable_hash(changed)


def test_l2_phase9_dataclass_defaults_do_not_use_mutable_values():
    for name, item in build_all_phase9_objects().items():
        for field in fields(item):
            assert not isinstance(field.default, (dict, list, set)), (name, field.name)
