from tiangong_kernel.l6_plugins.product_delivery import *

def test_model_requirement_not_model_call():
    req = default_product_model_requirement()
    assert req.requirement_only is True
    assert req.contains_sdk_import is False
    assert req.raw_http_allowed is False
