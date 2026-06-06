from tiangong_kernel.l6_plugins.product_delivery import *

def test_product_delivery_plugin_is_not_executor():
    arch = ProductDeliveryGroupArchitecture()
    assert arch.materializes_real_artifact is False
    assert arch.creates_parallel_runtime is False
    assert all(item.product_delivery_plugin_is_not_executor for item in default_product_delivery_plugin_declarations())
