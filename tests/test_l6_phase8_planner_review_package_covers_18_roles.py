import pytest
from tiangong_kernel.l6_plugins.final_closure import L6PlannerReviewPackage, ALL_PLANNER_ROLES

def test_planner_review_package_covers_18_roles():
    pkg = L6PlannerReviewPackage()
    assert len(ALL_PLANNER_ROLES) == 18
    assert pkg.role_count == 18
    assert len(pkg.role_refs) == 18
    with pytest.raises(ValueError):
        L6PlannerReviewPackage(role_count=17)
