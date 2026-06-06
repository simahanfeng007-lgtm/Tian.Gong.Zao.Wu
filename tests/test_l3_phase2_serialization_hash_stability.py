from dataclasses import fields, replace

from l3_phase2_builders import build_l3_phase2_objects
from tiangong_kernel.l3_orchestration import ProgressMarker, orchestration_stable_hash, orchestration_stable_json


def test_l3_phase2_objects_are_stably_serializable_and_hashable():
    for name, item in build_l3_phase2_objects().items():
        payload = orchestration_stable_json(item)
        digest = orchestration_stable_hash(item)
        assert isinstance(payload, str), name
        assert len(digest) == 64, name
        assert orchestration_stable_hash(item) == digest, name


def test_l3_phase2_hash_changes_when_fact_changes():
    run_snapshot = build_l3_phase2_objects()["run_snapshot"]
    changed = replace(run_snapshot, progress_ratio=0.75)
    assert orchestration_stable_hash(run_snapshot) != orchestration_stable_hash(changed)


def test_l3_phase2_defaults_do_not_use_mutable_values():
    for name, item in build_l3_phase2_objects().items():
        for field in fields(item):
            assert not isinstance(field.default, (dict, list, set)), (name, field.name)
    for field in fields(ProgressMarker):
        assert not isinstance(field.default, (dict, list, set)), field.name
