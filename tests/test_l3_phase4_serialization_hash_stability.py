from dataclasses import replace

from l3_phase4_builders import build_l3_phase4_objects
from tiangong_kernel.l3_orchestration import orchestration_stable_hash, orchestration_stable_json


def test_l3_phase4_objects_have_stable_json_and_hash():
    objects = build_l3_phase4_objects()
    targets = (
        objects["model_envelope"],
        objects["tool_envelope"],
        objects["action_envelope"],
        objects["validation_advice"],
        objects["math_result"],
        objects["route_ranking"],
        objects["recommendation"],
    )
    for target in targets:
        assert orchestration_stable_json(target) == orchestration_stable_json(target)
        assert orchestration_stable_hash(target) == orchestration_stable_hash(target)
    changed = replace(objects["route_candidate_1"], readiness_score=0.1)
    assert orchestration_stable_hash(changed) != orchestration_stable_hash(objects["route_candidate_1"])
