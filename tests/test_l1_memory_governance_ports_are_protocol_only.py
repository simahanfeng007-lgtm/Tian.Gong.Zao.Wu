from __future__ import annotations

from inspect import isabstract

import pytest

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l1_ports.memory_governance_ports import (
    ForgettingGovernancePort,
    ForgettingGovernanceRequest,
    ForgettingGovernanceResponse,
    MemoryGovernancePort,
    MemoryGovernanceRequest,
    MemoryGovernanceResponse,
)


def _ref(suffix: int, ref_type: str = "memory_governance") -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), ref_type)


def test_l1_memory_governance_requests_and_responses_do_not_execute() -> None:
    memory_request = MemoryGovernanceRequest(_ref(1), memory_refs=(_ref(2),))
    memory_response = MemoryGovernanceResponse(_ref(3), governance_refs=(_ref(4),))
    forgetting_request = ForgettingGovernanceRequest(_ref(5), forgetting_refs=(_ref(6),), tombstone_refs=(_ref(7),))
    forgetting_response = ForgettingGovernanceResponse(_ref(8), evidence_refs=(_ref(9),))

    assert memory_request.request_only is True
    assert memory_response.response_only is True
    assert memory_response.performs_governance is False
    assert forgetting_request.request_only is True
    assert forgetting_response.executes_forgetting is False
    assert forgetting_response.deletes_memory is False

    with pytest.raises(ValueError):
        ForgettingGovernanceResponse(_ref(10), executes_forgetting=True)
    with pytest.raises(ValueError):
        ForgettingGovernanceResponse(_ref(11), deletes_memory=True)


def test_l1_memory_governance_ports_are_abstract() -> None:
    assert isabstract(MemoryGovernancePort)
    assert isabstract(ForgettingGovernancePort)
    with pytest.raises(TypeError):
        MemoryGovernancePort()
