from pathlib import Path

from l3_phase5_builders import build_l3_phase5_objects


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "docs" / "l3_phase1_l0_l1_l2_hash_before.txt"
CURRENT = ROOT / "docs" / "l3_phase1_l0_l1_l2_hash_after.txt"


def test_l3_phase5_does_not_modify_l0_l1_l2_hash_evidence():
    assert BASELINE.read_text(encoding="utf-8") == CURRENT.read_text(encoding="utf-8")
    assert "MATCH" in (ROOT / "docs" / "l3_phase1_l0_l1_l2_hash_compare.txt").read_text(encoding="utf-8")


def test_l3_phase5_objects_keep_l2_math_affective_dynamic_inputs_as_refs():
    objects = build_l3_phase5_objects()
    math_input = objects["math_input"]
    assert math_input.affective_input is objects["phase3"]["math_input"].affective_input
    assert math_input.dynamic_drive_input is objects["phase3"]["math_input"].dynamic_drive_input
    assert math_input.intent_math_result is objects["phase4"]["math_result"]
    assert math_input.skill_tool_math_result is objects["phase3"]["math_result"]
