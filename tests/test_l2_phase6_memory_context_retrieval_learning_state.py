from dataclasses import FrozenInstanceError, MISSING, fields, is_dataclass
from enum import Enum
import inspect

import pytest

import tiangong_kernel.l2_state.context_state as context_state
import tiangong_kernel.l2_state.knowledge_reference_state as knowledge_reference_state
import tiangong_kernel.l2_state.learning_state as learning_state
import tiangong_kernel.l2_state.memory_state as memory_state
import tiangong_kernel.l2_state.retrieval_state as retrieval_state
from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l2_state import (
    ContextBudgetState,
    ContextCompressionState,
    ContextCompressionStatus,
    ContextContinuityState,
    ContextContinuityStatus,
    ContextInjectionState,
    ContextInjectionStatus,
    ContextOverflowStatus,
    ContextSegmentKind,
    ContextSegmentState,
    ContextVisibilityStatus,
    ContextWindowState,
    KnowledgeReferenceKind,
    KnowledgeReferenceState,
    KnowledgeReferenceVisibility,
    L2StateIdentity,
    L2StateKind,
    L2StateStatus,
    L2StateStatusKind,
    LearningBoundaryState,
    LearningBoundaryStatus,
    LearningMaterialKind,
    LearningMaterialRefState,
    LearningNeedState,
    LearningReadinessState,
    LearningReadinessStatus,
    LearningSignalKind,
    LearningSignalState,
    LearningVisibilityState,
    LearningVisibilityStatus,
    MemoryHealthState,
    MemoryHealthStatus,
    MemoryInjectionState,
    MemoryInjectionStatus,
    MemoryLayer,
    MemoryLayerState,
    MemoryRecallState,
    MemoryRecallStatus,
    MemoryRefState,
    MemoryVisibilityStatus,
    RetrievalChannelKind,
    RetrievalChannelState,
    RetrievalChannelStatus,
    RetrievalCoverageState,
    RetrievalPrivacyLevel,
    RetrievalQualityState,
    RetrievalQualityStatus,
    RetrievalQueryKind,
    RetrievalQueryState,
    RetrievalRequestState,
    RetrievalResultRefState,
    RetrievalStatus,
)


PHASE6_MODULES = (
    memory_state,
    context_state,
    retrieval_state,
    learning_state,
    knowledge_reference_state,
)


def ref(prefix: str, index: int) -> RefId:
    return RefId(f"{prefix}:{index:032x}")


def typed(index: int, ref_type: str) -> TypedRef:
    return TypedRef(ref("phase6", index), ref_type)


def identity(index: int, kind: L2StateKind = L2StateKind.MEMORY_CONTEXT) -> L2StateIdentity:
    return L2StateIdentity(state_ref=typed(index, kind.value), kind=kind)


def status() -> L2StateStatus:
    return L2StateStatus(kind=L2StateStatusKind.DECLARED, reason="phase6 fixture")


def build_phase6_objects():
    memory_ref = typed(10, "memory")
    context_ref = typed(20, "context_window")
    retrieval_request_ref = typed(30, "retrieval_request")
    retrieval_query_ref = typed(31, "retrieval_query")
    retrieval_result_ref = typed(32, "retrieval_result")
    learning_signal_ref = typed(40, "learning_signal")
    learning_need_ref = typed(41, "learning_need")
    material_ref = typed(42, "learning_material")
    knowledge_ref = typed(50, "knowledge_ref")

    memory_layer = MemoryLayerState(
        identity=identity(100),
        status=status(),
        layer=MemoryLayer.STABLE,
        scope_ref=typed(101, "scope"),
        memory_ref_count=1,
        visible_memory_refs=(memory_ref,),
        budget_limit=4096,
        budget_used=256,
    )
    memory = MemoryRefState(
        identity=identity(110),
        status=status(),
        memory_ref_id=memory_ref,
        layer=MemoryLayer.STABLE,
        scope_ref=typed(111, "scope"),
        source_ref=typed(112, "conversation"),
        content_hash="sha256:memory",
        summary="stable memory ref summary",
        visibility=MemoryVisibilityStatus.VISIBLE,
        confidence=0.8,
        freshness="fresh",
        created_at_ref=typed(113, "time"),
        updated_at_ref=typed(114, "time"),
    )
    recall = MemoryRecallState(
        identity=identity(120),
        status=status(),
        recall_id=typed(121, "memory_recall"),
        query_ref=retrieval_query_ref,
        requested_layers=(MemoryLayer.STABLE, MemoryLayer.RULE_LIKE),
        matched_refs=(memory_ref,),
        recall_status=MemoryRecallStatus.MATCHED,
        coverage_score=0.75,
        noise_score=0.1,
        reason_summary="matched by external state reference",
    )
    memory_injection = MemoryInjectionState(
        identity=identity(130),
        status=status(),
        injection_id=typed(131, "memory_injection"),
        injected_memory_refs=(memory_ref,),
        target_context_ref=context_ref,
        visibility_status=MemoryVisibilityStatus.INJECTED,
        budget_used=128,
        injection_status=MemoryInjectionStatus.INJECTED,
    )
    memory_health = MemoryHealthState(
        identity=identity(140),
        status=status(),
        health_ref=typed(141, "memory_health"),
        related_memory_refs=(memory_ref,),
        stale_count=0,
        conflict_count=0,
        missing_ref_count=0,
        over_budget_count=0,
        health_status=MemoryHealthStatus.HEALTHY,
    )

    segment = ContextSegmentState(
        identity=identity(200),
        status=status(),
        segment_id=typed(201, "context_segment"),
        kind=ContextSegmentKind.MEMORY_REF,
        source_ref=memory_ref,
        content_hash="sha256:segment",
        token_estimate=128,
        visibility=ContextVisibilityStatus.VISIBLE,
        importance_score=0.7,
        freshness="fresh",
        summary="memory ref segment",
    )
    budget = ContextBudgetState(
        identity=identity(210),
        status=status(),
        budget_ref=typed(211, "context_budget"),
        max_budget=8192,
        used_budget=1024,
        reserved_budget=512,
        memory_reserved_budget=256,
        retrieval_reserved_budget=128,
        observation_reserved_budget=128,
        overflow_status=ContextOverflowStatus.WITHIN_BUDGET,
    )
    window = ContextWindowState(
        identity=identity(220),
        status=status(),
        window_id=context_ref,
        active_segments=(segment.identity.state_ref,),
        max_budget=8192,
        used_budget=1024,
        reserved_budget=512,
        overflow_status=ContextOverflowStatus.WITHIN_BUDGET,
        budget_state_ref=budget.identity.state_ref,
        visibility=ContextVisibilityStatus.VISIBLE,
    )
    compression = ContextCompressionState(
        identity=identity(230),
        status=status(),
        compression_id=typed(231, "context_compression"),
        source_segments=(segment.identity.state_ref,),
        compressed_ref=typed(232, "context_summary_ref"),
        compression_status=ContextCompressionStatus.COMPRESSED,
        loss_risk=0.2,
        coverage_score=0.9,
    )
    context_injection = ContextInjectionState(
        identity=identity(240),
        status=status(),
        injection_id=typed(241, "context_injection"),
        source_refs=(memory_injection.identity.state_ref,),
        target_window_ref=window.identity.state_ref,
        injection_status=ContextInjectionStatus.INJECTED,
        budget_delta=128,
        visibility_status=ContextVisibilityStatus.INJECTED,
    )
    continuity = ContextContinuityState(
        identity=identity(250),
        status=status(),
        continuity_id=typed(251, "context_continuity"),
        previous_window_ref=typed(252, "context_window"),
        current_window_ref=window.identity.state_ref,
        carryover_refs=(segment.identity.state_ref,),
        broken_refs=(),
        continuity_status=ContextContinuityStatus.CONTINUOUS,
    )

    channel = RetrievalChannelState(
        identity=identity(300),
        status=status(),
        channel_ref=typed(301, "retrieval_channel"),
        channel_kind=RetrievalChannelKind.MEMORY,
        channel_status=RetrievalChannelStatus.AVAILABLE,
        scope_ref=typed(302, "scope"),
        observation_source_refs=(typed(303, "observation_source"),),
        trust_label="trusted_by_boundary",
        freshness="fresh",
    )
    request = RetrievalRequestState(
        identity=identity(310),
        status=status(),
        request_id=retrieval_request_ref,
        requester_ref=typed(311, "model_request"),
        channel_kinds=(RetrievalChannelKind.MEMORY, RetrievalChannelKind.OBSERVATION_STREAM),
        query_hash="sha256:query",
        query_summary="retrieve memory and observation references",
        retrieval_status=RetrievalStatus.RESULT_REFERENCED,
    )
    query = RetrievalQueryState(
        identity=identity(320),
        status=status(),
        query_id=retrieval_query_ref,
        query_kind=RetrievalQueryKind.HYBRID,
        normalized_hash="sha256:normalized",
        language="zh-CN",
        expected_scope="current run state refs",
        privacy_level=RetrievalPrivacyLevel.INTERNAL,
        source_request_ref=request.identity.state_ref,
    )
    result = RetrievalResultRefState(
        identity=identity(330),
        status=status(),
        result_ref_id=retrieval_result_ref,
        source_ref=memory_ref,
        channel_kind=RetrievalChannelKind.MEMORY,
        rank=1,
        score=0.88,
        snippet_hash="sha256:snippet",
        summary="memory reference result",
        freshness="fresh",
        trust_level="trusted",
        request_state_ref=request.identity.state_ref,
        query_state_ref=query.identity.state_ref,
    )
    coverage = RetrievalCoverageState(
        identity=identity(340),
        status=status(),
        coverage_id=typed(341, "retrieval_coverage"),
        requested_scope="memory observation",
        covered_scope="memory",
        missing_scope="none",
        coverage_score=0.8,
        result_refs=(result.identity.state_ref,),
    )
    quality = RetrievalQualityState(
        identity=identity(350),
        status=status(),
        quality_id=typed(351, "retrieval_quality"),
        precision_hint=0.8,
        recall_hint=0.7,
        freshness_score=0.9,
        trust_score=0.85,
        noise_score=0.1,
        quality_status=RetrievalQualityStatus.USABLE,
        evidence_result_refs=(result.identity.state_ref,),
    )

    signal = LearningSignalState(
        identity=identity(400),
        status=status(),
        signal_id=learning_signal_ref,
        kind=LearningSignalKind.RETRIEVAL_GAP,
        source_ref=coverage.identity.state_ref,
        summary="retrieval gap reference only",
        strength=0.6,
        urgency=0.4,
        related_retrieval_refs=(coverage.identity.state_ref,),
    )
    need = LearningNeedState(
        identity=identity(410),
        status=status(),
        need_id=learning_need_ref,
        signal_refs=(signal.identity.state_ref,),
        target_domain="context retrieval state",
        expected_use="future state interpretation",
        missing_knowledge_summary="missing reference interpretation rule",
        missing_tool_summary="no tool production requested",
        readiness_status=LearningReadinessStatus.MATERIAL_MISSING,
        risk_hint="A1 ref-only",
    )
    material = LearningMaterialRefState(
        identity=identity(420),
        status=status(),
        material_ref_id=material_ref,
        source_ref=result.identity.state_ref,
        material_kind=LearningMaterialKind.OBSERVATION_REF,
        content_hash="sha256:material",
        summary="observation material reference",
        freshness="fresh",
        trust_level="trusted",
        related_need_ref=need.identity.state_ref,
    )
    readiness = LearningReadinessState(
        identity=identity(430),
        status=status(),
        readiness_id=typed(431, "learning_readiness"),
        need_ref=need.identity.state_ref,
        available_material_refs=(material.identity.state_ref,),
        missing_material_summary="none for state fixture",
        evidence_refs=(result.identity.state_ref,),
        readiness_score=0.5,
        readiness_status=LearningReadinessStatus.DECLARED,
    )
    learning_boundary = LearningBoundaryState(
        identity=identity(440),
        status=status(),
        boundary_ref=typed(441, "learning_boundary"),
        learning_refs=(signal.identity.state_ref, need.identity.state_ref),
        boundary_label=LearningBoundaryStatus.RECORDABLE,
        reason_summary="state recording only",
        evidence_refs=(readiness.identity.state_ref,),
    )
    learning_visibility = LearningVisibilityState(
        identity=identity(450),
        status=status(),
        visibility_id=typed(451, "learning_visibility"),
        learning_refs=(signal.identity.state_ref, need.identity.state_ref),
        visible_to_model=True,
        visible_to_human=True,
        visibility_status=LearningVisibilityStatus.LIMITED,
        reason_summary="ref-only visibility",
    )

    knowledge = KnowledgeReferenceState(
        identity=identity(500),
        status=status(),
        knowledge_ref_id=knowledge_ref,
        source_ref=material.identity.state_ref,
        knowledge_kind=KnowledgeReferenceKind.METHOD,
        content_hash="sha256:knowledge",
        summary="knowledge reference only",
        visibility=KnowledgeReferenceVisibility.REF_VISIBLE,
        freshness="fresh",
        trust_level="trusted",
        related_learning_ref=need.identity.state_ref,
        related_retrieval_ref=result.identity.state_ref,
    )

    return {
        "memory_layer": memory_layer,
        "memory": memory,
        "recall": recall,
        "memory_injection": memory_injection,
        "memory_health": memory_health,
        "segment": segment,
        "budget": budget,
        "window": window,
        "compression": compression,
        "context_injection": context_injection,
        "continuity": continuity,
        "channel": channel,
        "request": request,
        "query": query,
        "result": result,
        "coverage": coverage,
        "quality": quality,
        "signal": signal,
        "need": need,
        "material": material,
        "readiness": readiness,
        "learning_boundary": learning_boundary,
        "learning_visibility": learning_visibility,
        "knowledge": knowledge,
    }


def _public_local_classes(module):
    for _, value in inspect.getmembers(module, inspect.isclass):
        if value.__module__ == module.__name__ and not value.__name__.startswith("_"):
            yield value


def test_l2_phase6_all_new_state_objects_can_be_instantiated():
    objects = build_phase6_objects()
    assert len(objects) == 24
    assert objects["memory"].layer is MemoryLayer.STABLE
    assert objects["recall"].recall_status is MemoryRecallStatus.MATCHED
    assert objects["memory_injection"].injection_status is MemoryInjectionStatus.INJECTED
    assert objects["memory_health"].health_status is MemoryHealthStatus.HEALTHY
    assert objects["segment"].kind is ContextSegmentKind.MEMORY_REF
    assert objects["window"].overflow_status is ContextOverflowStatus.WITHIN_BUDGET
    assert objects["compression"].compression_status is ContextCompressionStatus.COMPRESSED
    assert objects["context_injection"].injection_status is ContextInjectionStatus.INJECTED
    assert objects["continuity"].continuity_status is ContextContinuityStatus.CONTINUOUS
    assert objects["channel"].channel_status is RetrievalChannelStatus.AVAILABLE
    assert objects["request"].retrieval_status is RetrievalStatus.RESULT_REFERENCED
    assert objects["query"].query_kind is RetrievalQueryKind.HYBRID
    assert objects["result"].channel_kind is RetrievalChannelKind.MEMORY
    assert objects["quality"].quality_status is RetrievalQualityStatus.USABLE
    assert objects["signal"].kind is LearningSignalKind.RETRIEVAL_GAP
    assert objects["need"].readiness_status is LearningReadinessStatus.MATERIAL_MISSING
    assert objects["material"].material_kind is LearningMaterialKind.OBSERVATION_REF
    assert objects["learning_boundary"].boundary_label is LearningBoundaryStatus.RECORDABLE
    assert objects["learning_visibility"].visibility_status is LearningVisibilityStatus.LIMITED
    assert objects["knowledge"].knowledge_kind is KnowledgeReferenceKind.METHOD


def test_l2_phase6_public_state_dataclasses_are_frozen_and_slotted():
    violations = []
    dataclasses = []
    for module in PHASE6_MODULES:
        for cls in _public_local_classes(module):
            if issubclass(cls, Enum):
                continue
            dataclasses.append(cls.__name__)
            if not is_dataclass(cls):
                violations.append((cls.__name__, "not_dataclass"))
                continue
            if not cls.__dataclass_params__.frozen:
                violations.append((cls.__name__, "not_frozen"))
            if "__slots__" not in cls.__dict__:
                violations.append((cls.__name__, "no_slots"))
    assert len(dataclasses) == 24
    assert violations == []


def test_l2_phase6_objects_reject_mutation():
    item = build_phase6_objects()["memory"]
    with pytest.raises(FrozenInstanceError):
        item.summary = "changed"


def test_l2_phase6_defaults_do_not_share_mutable_values():
    violations = []
    for module in PHASE6_MODULES:
        for cls in _public_local_classes(module):
            if issubclass(cls, Enum) or not is_dataclass(cls):
                continue
            for item in fields(cls):
                if item.default is not MISSING and isinstance(item.default, (list, dict, set)):
                    violations.append((cls.__name__, item.name, type(item.default).__name__))
    assert violations == []


def test_l2_phase6_numeric_guards_reject_invalid_scores_and_counts():
    with pytest.raises(ValueError):
        MemoryRefState(identity=identity(900), status=status(), confidence=1.1)
    with pytest.raises(ValueError):
        ContextSegmentState(identity=identity(901), status=status(), token_estimate=-1)
    with pytest.raises(ValueError):
        RetrievalResultRefState(identity=identity(902), status=status(), score=-0.1)
    with pytest.raises(ValueError):
        LearningSignalState(identity=identity(903), status=status(), urgency=2.0)
