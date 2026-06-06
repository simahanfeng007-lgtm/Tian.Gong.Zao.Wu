import pytest
from tiangong_kernel.l6_plugins.product_delivery import *

def test_delivery_package_candidate_not_zip():
    package = DeliveryPackageCandidate()
    assert package.real_archive_created is False
    with pytest.raises(ValueError):
        DeliveryPackageCandidate(real_archive_created=True)
