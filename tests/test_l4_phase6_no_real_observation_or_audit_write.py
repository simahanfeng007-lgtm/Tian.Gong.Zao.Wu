from pathlib import Path

from l4_phase6_builders import audit_ref, observation_ref
from tiangong_kernel.l4_action_grounding import NoAuditWriteInL4Invariant, NoRealObservationInL4Invariant


def test_l4_phase6_no_real_observation_or_audit_write_objects():
    obs = observation_ref()
    audit = audit_ref()
    observation_invariant = NoRealObservationInL4Invariant(invariant_ref=obs.observation_ref)
    audit_invariant = NoAuditWriteInL4Invariant(invariant_ref=audit.audit_ref)

    assert obs.samples_real_observation is False
    assert obs.reads_real_screen is False
    assert audit.writes_real_audit is False
    assert audit.writes_audit_store is False
    assert observation_invariant.l4_can_override is False
    assert audit_invariant.l4_can_override is False


def test_l4_phase6_static_source_has_no_real_observation_or_audit_write_terms():
    root = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l4_action_grounding"
    phase6_source = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py") if "execution_" in path.name or "observation" in path.name)
    assert "samples_real_observation: bool = True" not in phase6_source
    assert "writes_real_audit: bool = True" not in phase6_source
    assert "writes_audit_store: bool = True" not in phase6_source
