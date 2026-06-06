from tiangong_kernel.l5_plugin_host import PluginIsolationDispositionValidator, PluginPhase6ConflictKind, has_forbidden_phase6_method, phase6_public_text_is_safe
from l5_phase6_factories import disposition, projection


def test_isolation_disposition_is_declarative_and_no_live_state_mutation():
    obj = disposition()
    assert not has_forbidden_phase6_method(obj)
    assert PluginIsolationDispositionValidator().review(obj) == tuple()
    bad = disposition(disposition_kind_ref="file:///tmp/live")
    conflicts = PluginIsolationDispositionValidator().review(bad)
    assert any(c.kind == PluginPhase6ConflictKind.DISPOSITION_LIVE_ISOLATE_CONFLICT for c in conflicts)
    assert any(c.severity.value == "p0" for c in conflicts)


def test_public_projection_minimal_disclosure_and_redacted_evidence_refs():
    obj = projection()
    assert phase6_public_text_is_safe(obj)
    assert obj.redacted_evidence_refs
    assert all(ref.startswith("redacted_evidence:") for ref in obj.redacted_evidence_refs)
    text = str(obj)
    for forbidden in ("raw_log", "permit_object", "lease_object", "confirmation_ticket", "module:function"):
        assert forbidden not in text
