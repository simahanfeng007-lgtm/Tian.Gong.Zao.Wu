from pathlib import Path

from l3_phase8_builders import build_l3_phase8_objects

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "docs" / "l3_phase1_l0_l1_l2_hash_before.txt"
CURRENT = ROOT / "docs" / "l3_phase1_l0_l1_l2_hash_after.txt"


def test_l3_phase8_does_not_modify_l0_l1_l2_hash_evidence():
    assert BASELINE.read_text(encoding="utf-8") == CURRENT.read_text(encoding="utf-8")
    assert "MATCH" in (ROOT / "docs" / "l3_phase1_l0_l1_l2_hash_compare.txt").read_text(encoding="utf-8")


def test_l3_phase8_handoff_objects_connect_to_prior_stage_refs_only():
    objects = build_l3_phase8_objects()
    assert objects["l4_request_bundle"].request_refs[0] == objects["phase5"]["execution_ref"].request_ref
    assert objects["l5_request_bundle"].request_refs[0] == objects["phase5"]["boundary_ref"].request_ref
    assert objects["l6_request_bundle"].observation_requests[0].source_ref == objects["phase6"]["observation_ref"].observation_ref
    assert objects["projection"].summary_projection.step_ref == objects["phase7"]["step_ref"]
