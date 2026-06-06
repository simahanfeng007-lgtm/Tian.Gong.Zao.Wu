import pytest
from l5_phase7_builders import phase7_projection
from tiangong_kernel.l5_plugin_host import PluginPhase7PublicProjection


def test_phase7_public_projection_minimal_disclosure():
    projection = phase7_projection()
    assert projection.redacted_evidence_refs
    assert projection.projection_digest


def test_phase7_public_projection_rejects_url_leak():
    with pytest.raises(ValueError):
        PluginPhase7PublicProjection(projection_ref="projection:bad", l4_handoff_summary=(("url", "https://leak.invalid"),))
