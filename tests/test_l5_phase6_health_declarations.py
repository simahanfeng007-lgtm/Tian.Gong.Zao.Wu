from dataclasses import replace
from tiangong_kernel.l5_plugin_host import PluginHealthValidator, PluginPhase6ConflictKind, has_forbidden_phase6_method, phase6_declaration_digest, to_l5_digest
from l5_phase6_factories import signal, check


def test_health_signal_declaration_is_inert_and_digest_stable():
    obj = signal()
    assert obj.no_live_probe_ref
    assert not has_forbidden_phase6_method(obj)
    assert obj.health_signal_digest == signal().health_signal_digest
    assert phase6_declaration_digest(replace(obj, signal_semantics_ref="semantics:changed"), ("health_signal_digest",)) != phase6_declaration_digest(obj, ("health_signal_digest",))


def test_health_check_declaration_no_live_probe_and_requires_readiness():
    report = PluginHealthValidator().assess(health_signals=(signal(),), health_checks=(check(readiness_decl_ref=""),))
    assert not report.passed
    assert any(PluginPhase6ConflictKind.HEALTH_CHECK_MISSING_READINESS_DECL_CONFLICT.value in ref for ref in report.conflict_refs)


def test_health_assessment_is_pure_and_requires_audit_evidence_chain():
    sig = signal()
    chk = check()
    before = (to_l5_digest(sig), to_l5_digest(chk))
    report = PluginHealthValidator().assess(health_signals=(sig,), health_checks=(chk,))
    assert report.passed
    assert (to_l5_digest(sig), to_l5_digest(chk)) == before
    bad_report = PluginHealthValidator().assess(health_signals=(signal(actor_ref=""),), health_checks=(chk,))
    assert bad_report.p1_count >= 1
    assert any(PluginPhase6ConflictKind.AUDIT_EVIDENCE_CHAIN_MISSING_CONFLICT.value in ref for ref in bad_report.conflict_refs)
