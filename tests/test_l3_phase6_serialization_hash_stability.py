from dataclasses import replace

from l3_phase6_builders import build_l3_phase6_objects
from tiangong_kernel.l3_orchestration import orchestration_stable_hash, orchestration_stable_json


def test_l3_phase6_objects_have_stable_json_and_hash():
    objects = build_l3_phase6_objects()
    targets = (
        objects["observation_envelope"],
        objects["context_carryover"],
        objects["subsystem_request"],
        objects["memory_request"],
        objects["retrieval_request"],
        objects["learning_request"],
        objects["affective_request"],
        objects["candidate_proposal"],
        objects["recommendation"],
    )
    for target in targets:
        assert orchestration_stable_json(target) == orchestration_stable_json(target)
        assert orchestration_stable_hash(target) == orchestration_stable_hash(target)
    changed = replace(objects["candidate_proposal"], priority_hint=0.1)
    assert orchestration_stable_hash(changed) != orchestration_stable_hash(objects["candidate_proposal"])
