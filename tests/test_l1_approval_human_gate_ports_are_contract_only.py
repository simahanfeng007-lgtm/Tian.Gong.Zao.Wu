import inspect
from dataclasses import FrozenInstanceError, is_dataclass

import pytest

from tiangong_kernel.l1_ports import (
    ApprovalBoundaryPort,
    ApprovalRequest,
    ApprovalResponse,
    HumanGateBoundaryPort,
    HumanGateRequest,
    HumanGateResponse,
)


def test_l1_approval_human_gate_ports_are_contract_only():
    assert inspect.isabstract(ApprovalBoundaryPort)
    assert inspect.isabstract(HumanGateBoundaryPort)
    for cls in (ApprovalRequest, ApprovalResponse, HumanGateRequest, HumanGateResponse):
        item = cls()
        assert is_dataclass(item)
        assert hasattr(type(item), "__slots__")
        with pytest.raises(FrozenInstanceError):
            item.schema_version = "changed"
    assert ApprovalResponse().grants_permission is False
    assert ApprovalResponse().issues_ticket is False
    assert HumanGateResponse().confirms_action is False
