from pathlib import Path


FORBIDDEN_TERMS = (
    "Runtime",
    "绁炴灑",
    "AbilityPackage",
    "CapabilityPort",
    "AbilityPackagePort",
    "subprocess",
    "socket",
    "requests",
    "urllib",
    "httpx",
    "open(",
    "write_text",
    "write_bytes",
    "Popen",
    ".get(",
    ".post(",
    ".request(",
    ".connect(",
    "tiangong_kernel.l5",
    "tiangong_kernel.l6",
)


PHASE6_FILE_NAMES = (
    "action_failure_return_envelope.py",
    "action_outcome_envelope.py",
    "action_result_return_envelope.py",
    "boundary_feedback_ref.py",
    "cancellation_timeout_fake.py",
    "execution_audit_ref.py",
    "execution_cancellation.py",
    "execution_evidence_ref.py",
    "execution_observation_ref.py",
    "execution_resource_usage.py",
    "execution_resume_ref.py",
    "execution_retry_advice.py",
    "execution_return_projection.py",
    "execution_rollback_hint.py",
    "execution_timeout.py",
    "execution_trace_ref.py",
    "failure_category.py",
    "failure_recoverability_hint.py",
    "failure_severity.py",
    "l3_replan_suggestion_ref.py",
    "observation_reference_fake.py",
    "observation_return_envelope.py",
    "phase6_invariants.py",
    "recovery_requirement_ref.py",
    "result_failure_normalization.py",
)


def test_l4_phase6_has_no_legacy_or_real_action_terms():
    root = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l4_action_grounding"
    source = "\n".join((root / name).read_text(encoding="utf-8") for name in PHASE6_FILE_NAMES)
    for term in FORBIDDEN_TERMS:
        assert term not in source
