from tiangong_kernel.l6_plugins.product_delivery import *

def test_tool_requirement_not_tool_call():
    req = default_product_tool_requirement()
    assert req.requirement_only is True
    assert req.invokes_tool is False
    assert req.stores_tool_handle is False
