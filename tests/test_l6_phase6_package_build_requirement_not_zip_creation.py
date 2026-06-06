import pytest
from tiangong_kernel.l6_plugins.product_delivery import *

def test_package_build_requirement_not_zip_creation():
    req = PackageBuildRequirement()
    assert req.materializes_archive is False
    with pytest.raises(ValueError):
        PackageBuildRequirement(materializes_archive=True)
