import tiangong_kernel.l2_state as l2_state
from l2_phase9_builders import build_affective_objects, build_all_phase9_objects, build_dynamic_drive_objects, build_math_objects, identity, status, typed
from tiangong_kernel.l0_primitives.serialization import stable_hash
from tiangong_kernel.l2_state import (
    AffectiveColorState,
    DynamicWeightState,
    L2StateCatalog,
    L2StateDomain,
    L2StateIdentity,
    L2StateKind,
    ModelVisibleStateProjection,
    ProjectionStatus,
    StateDomainCatalog,
    StateObjectMeta,
)


def test_l2_phase9_public_exports_include_math_affective_dynamic_objects():
    required = {
        "MathFeatureState",
        "MathObjectiveState",
        "MathConstraintState",
        "MathScoreState",
        "MathEvaluationState",
        "MathRecommendationState",
        "MathModelRefState",
        "EmotionBaseState",
        "AffectiveColorState",
        "AffectiveBoundaryState",
        "DynamicWeightState",
        "SystemDriveState",
        "ExecutionReadinessState",
        "DynamicDriveEvaluationRefState",
    }
    assert required.issubset(set(l2_state.__all__))
    for name in required:
        assert hasattr(l2_state, name), name


def test_l2_phase9_new_state_kinds_and_domain_are_available_without_removing_old_kinds():
    assert L2StateKind.RUN.value == "run"
    assert L2StateKind.PROJECTION.value == "projection"
    assert L2StateKind.MATH.value == "math"
    assert L2StateKind.AFFECTIVE.value == "affective"
    assert L2StateKind.DYNAMIC_DRIVE.value == "dynamic_drive"
    assert L2StateDomain.MATH_AFFECTIVE_DYNAMIC_DRIVE.value == "math_affective_dynamic_drive"


def test_l2_phase9_catalog_can_reference_new_patch_domain():
    meta = StateObjectMeta(
        identity=identity(400, L2StateKind.CATALOG),
        status=status(),
        object_name="MathFeatureState",
        module_ref=typed(401, "module"),
        domain=L2StateDomain.MATH_AFFECTIVE_DYNAMIC_DRIVE,
        phase="9",
        summary="phase9 object meta",
    )
    domain_catalog = StateDomainCatalog(
        identity=identity(402, L2StateKind.CATALOG),
        status=status(),
        catalog_id=typed(403, "catalog"),
        domain=L2StateDomain.MATH_AFFECTIVE_DYNAMIC_DRIVE,
        state_objects=(meta,),
        summary="phase9 domain catalog",
    )
    catalog = L2StateCatalog(
        identity=identity(404, L2StateKind.CATALOG),
        status=status(),
        catalog_id=typed(405, "catalog"),
        domains=(domain_catalog,),
        total_object_count=1,
        public_object_count=1,
        deprecated_object_count=0,
    )
    assert stable_hash(catalog)
    assert catalog.domains[0].state_objects[0].object_name == "MathFeatureState"


def test_l2_phase9_projection_accepts_math_affective_dynamic_refs():
    math = build_math_objects()["evaluation"]
    affective = build_affective_objects()["color"]
    dynamic = build_dynamic_drive_objects()["weight"]
    projection = ModelVisibleStateProjection(
        identity=identity(410, L2StateKind.PROJECTION),
        status=status(),
        projection_id=typed(411, "projection"),
        math_state_refs=(math.identity.state_ref,),
        affective_state_refs=(affective.identity.state_ref,),
        dynamic_drive_refs=(dynamic.identity.state_ref,),
        projection_status=ProjectionStatus.PARTIAL,
    )
    assert isinstance(math.identity, L2StateIdentity)
    assert isinstance(affective, AffectiveColorState)
    assert isinstance(dynamic, DynamicWeightState)
    assert projection.math_state_refs == (math.identity.state_ref,)
    assert projection.affective_state_refs == (affective.identity.state_ref,)
    assert projection.dynamic_drive_refs == (dynamic.identity.state_ref,)


def test_l2_phase9_objects_integrate_with_full_l2_serialization_surface():
    for name, item in build_all_phase9_objects().items():
        assert len(stable_hash(item)) == 64, name
