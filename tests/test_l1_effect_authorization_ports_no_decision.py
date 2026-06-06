import inspect
from pathlib import Path

from tiangong_kernel.l1_ports import (
    ConstraintCheckPort,
    ContractReferencePort,
    EffectAuthorizationPort,
    EffectAuthorizationResponse,
    EffectPolicyReferencePort,
    EffectPolicyReferenceResponse,
)


def test_l1_effect_authorization_ports_are_abstract_and_no_decision():
    for cls in (EffectAuthorizationPort, EffectPolicyReferencePort, ContractReferencePort, ConstraintCheckPort):
        assert inspect.isabstract(cls)
    assert EffectAuthorizationResponse().grants_permission is False
    assert EffectPolicyReferenceResponse().policy_decision_made is False


def test_l1_effect_authorization_sources_have_no_upper_imports_or_execution():
    for file in (
        Path("tiangong_kernel/l1_ports/approval_human_gate_ports.py"),
        Path("tiangong_kernel/l1_ports/effect_authorization_ports.py"),
        Path("tiangong_kernel/l1_ports/contract_constraint_ports.py"),
    ):
        source = file.read_text(encoding="utf-8")
        for token in ("tiangong_kernel.l2_", "tiangong_kernel.l3_", "tiangong_kernel.l4_", "tiangong_kernel.l5", "tiangong_kernel.l6", "open(", "subprocess", "requests"):
            assert token not in source, (file, token)
