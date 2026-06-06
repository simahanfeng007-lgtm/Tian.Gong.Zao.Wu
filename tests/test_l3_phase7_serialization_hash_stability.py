from dataclasses import replace

from l3_phase7_builders import build_l3_phase7_objects
from tiangong_kernel.l3_orchestration import orchestration_stable_hash, orchestration_stable_json


def test_l3_phase7_objects_have_stable_json_and_hash():
    objects = build_l3_phase7_objects()
    targets = (
        objects["validation_request"],
        objects["validation_envelope"],
        objects["recovery_request"],
        objects["rollback_advice"],
        objects["experiment_request"],
        objects["iteration_request"],
        objects["evolution_request"],
        objects["self_learning"],
        objects["change_ref"],
        objects["validation_recovery_recommendation"],
        objects["iteration_evolution_recommendation"],
    )
    for target in targets:
        assert orchestration_stable_json(target) == orchestration_stable_json(target)
        assert orchestration_stable_hash(target) == orchestration_stable_hash(target)
    changed = replace(objects["validation_value"], value=0.1)
    assert orchestration_stable_hash(changed) != orchestration_stable_hash(objects["validation_value"])
