import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_audit_evidence_chain_required_on_outputs_and_quality_gate():
    output = MindOutputBase()
    assert output.evidence_refs
    assert output.trace_ref.startswith("ref:")
    assert output.audit_ref.startswith("audit:")
    assert output.responsibility_chain_ref.startswith("responsibility:")
    gate = L6Phase3MindQualityGateDecision()
    assert gate.audit_evidence_chain_passed is True
    assert gate.responsibility_chain_passed is True
    assert gate.tamper_evidence_chain_passed is True
