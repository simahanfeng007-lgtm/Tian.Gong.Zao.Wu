from dataclasses import fields, replace

from l3_phase1_builders import build_l3_objects
from tiangong_kernel.l3_orchestration import orchestration_stable_hash, orchestration_stable_json


def test_l3_phase1_objects_are_stably_serializable_and_hashable():
    for name, item in build_l3_objects().items():
        payload = orchestration_stable_json(item)
        digest = orchestration_stable_hash(item)
        assert isinstance(payload, str), name
        assert len(digest) == 64, name
        assert orchestration_stable_hash(item) == digest, name


def test_l3_phase1_hash_changes_when_fact_changes():
    score_vector = build_l3_objects()["score_vector"]
    changed = replace(score_vector, normalized_score=0.5)
    assert orchestration_stable_hash(score_vector) != orchestration_stable_hash(changed)


def test_l3_phase1_defaults_do_not_use_mutable_values():
    for name, item in build_l3_objects().items():
        for field in fields(item):
            assert not isinstance(field.default, (dict, list, set)), (name, field.name)
