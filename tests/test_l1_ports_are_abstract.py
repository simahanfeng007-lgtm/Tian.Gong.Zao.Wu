import inspect

import pytest

from tiangong_kernel.l1_ports import BasePort


def test_base_port_is_abstract_protocol_skeleton():
    assert inspect.isabstract(BasePort)
    abstract_methods = set(BasePort.__abstractmethods__)
    assert abstract_methods == {
        "identity",
        "describe_boundary",
        "describe_health",
        "describe_lifecycle",
    }
    with pytest.raises(TypeError):
        BasePort()
