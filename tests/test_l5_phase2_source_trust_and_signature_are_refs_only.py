import pytest

from tiangong_kernel.l5_plugin_host import PluginSignatureReference, PluginSourceTrustReference


def test_source_trust_and_signature_refs_do_not_mark_real_verification():
    trust = PluginSourceTrustReference(trust_ref="source_trust:declared")
    signature = PluginSignatureReference(signature_ref="signature:declared", digest_ref="digest:manifest")
    assert not trust.verified
    assert not signature.verified
    with pytest.raises(ValueError):
        PluginSourceTrustReference(trust_ref="source_trust:declared", verified=True)
    with pytest.raises(ValueError):
        PluginSignatureReference(signature_ref="signature:declared", verified=True)
