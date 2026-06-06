from pathlib import Path

from l3_phase7_builders import build_l3_phase7_objects

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "docs" / "l3_phase1_l0_l1_l2_hash_before.txt"
CURRENT = ROOT / "docs" / "l3_phase1_l0_l1_l2_hash_after.txt"


def test_l3_phase7_does_not_modify_l0_l1_l2_hash_evidence():
    assert BASELINE.read_text(encoding="utf-8") == CURRENT.read_text(encoding="utf-8")
    assert "MATCH" in (ROOT / "docs" / "l3_phase1_l0_l1_l2_hash_compare.txt").read_text(encoding="utf-8")


def test_l3_phase7_objects_connect_to_previous_stage_refs_only():
    objects = build_l3_phase7_objects()
    assert objects["validation_request"].target_refs[0].target_ref == objects["step_ref"]
    assert objects["recovery_request"].target_refs[0].target_ref == objects["execution_failure"].failure_ref
    assert objects["validation_math_input"].observation_result_refs == (objects["observation"].observation_ref,)
    assert objects["iteration_math_input"].candidate_refs == (objects["candidate"].candidate_ref,)
