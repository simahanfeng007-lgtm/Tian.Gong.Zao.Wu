import pytest
from tiangong_kernel.l6_plugins.product_delivery import *

def test_file_write_requirement_not_file_write():
    req = FileWriteRequirement()
    assert req.materializes_file is False
    with pytest.raises(ValueError):
        FileWriteRequirement(materializes_file=True)
