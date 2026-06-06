from pathlib import Path

from l3_phase6_builders import build_l3_phase6_objects


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "docs" / "l3_phase1_l0_l1_l2_hash_before.txt"
CURRENT = ROOT / "docs" / "l3_phase1_l0_l1_l2_hash_after.txt"


def test_l3_phase6_does_not_modify_l0_l1_l2_hash_evidence():
    assert BASELINE.read_text(encoding="utf-8") == CURRENT.read_text(encoding="utf-8")
    assert "MATCH" in (ROOT / "docs" / "l3_phase1_l0_l1_l2_hash_compare.txt").read_text(encoding="utf-8")


def test_l3_phase6_objects_keep_prior_stage_refs_as_refs():
    objects = build_l3_phase6_objects()
    assert objects["phase5"]["execution_request"] is not None
    assert objects["subsystem_request"].request_ref.source_run_ref == objects["run_ref"]
    assert objects["observation_ref"].source_execution_result_ref == objects["phase5"]["result_ref"]
    assert objects["affective_input_ref"].source_weight_input is objects["phase5"]["phase3"]["math_input"].affective_input
