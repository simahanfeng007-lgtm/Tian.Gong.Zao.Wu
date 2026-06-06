from dataclasses import replace

from l3_phase5_builders import build_l3_phase5_objects
from tiangong_kernel.l3_orchestration import orchestration_stable_hash, orchestration_stable_json


def test_l3_phase5_objects_have_stable_json_and_hash():
    objects = build_l3_phase5_objects()
    targets = (
        objects["boundary_request"],
        objects["boundary_envelope"],
        objects["execution_request"],
        objects["dispatch_request"],
        objects["math_result"],
        objects["recommendation"],
    )
    for target in targets:
        assert orchestration_stable_json(target) == orchestration_stable_json(target)
        assert orchestration_stable_hash(target) == orchestration_stable_hash(target)
    changed = replace(objects["execution_candidate_1"], readiness_score=0.1)
    assert orchestration_stable_hash(changed) != orchestration_stable_hash(objects["execution_candidate_1"])
