from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps
from tiangong_kernel.l2_state import (
    AuditObservationKind,
    AuditObservationState,
    AuditObservationStatus,
    EventStreamKind,
    EventStreamState,
    EventStreamStatus,
    L2StateIdentity,
    L2StateKind,
    L2StateStatus,
    L2StateStatusKind,
    ObservationChannelKind,
    ObservationChannelState,
    ObservationChannelStatus,
    ObservationFrameKind,
    ObservationFrameState,
    ObservationFrameStatus,
    ObservationMetricKind,
    ObservationMetricState,
    ObservationMetricStatus,
    ObservationProjectionKind,
    ObservationProjectionState,
    ObservationProjectionStatus,
    ObservationQualityDimension,
    ObservationQualityState,
    ObservationQualityStatus,
    ObservationSourceKind,
    ObservationSourceState,
    ObservationSourceStatus,
)
from tests.test_l2_phase4_serialization import build_phase4_objects


def ref(prefix: str, index: int) -> RefId:
    return RefId(f"{prefix}:{index:032x}")


def typed(index: int, ref_type: str) -> TypedRef:
    return TypedRef(ref("phase5", index), ref_type)


def identity(index: int, kind: L2StateKind = L2StateKind.OBSERVATION) -> L2StateIdentity:
    return L2StateIdentity(state_ref=typed(index, kind.value), kind=kind)


def status() -> L2StateStatus:
    return L2StateStatus(kind=L2StateStatusKind.DECLARED, reason="phase5 fixture")


def build_phase5_chain():
    phase4 = build_phase4_objects()
    phase3 = phase4["phase3"]
    run_ref = phase3["run"].identity.state_ref
    task_ref = phase3["task"].identity.state_ref
    skill_ref = phase3["skill_activation"].identity.state_ref
    tool_group_ref = phase3["tool_release"].identity.state_ref
    tool_intent_ref = phase3["tool_intent"].identity.state_ref
    action_ref = phase3["action_intent"].identity.state_ref
    effect_ref = phase3["effect_observation"].identity.state_ref
    feedback_ref = phase3["feedback"].identity.state_ref
    boundary_ref = phase4["boundary_check"].identity.state_ref
    resource_ref = phase4["budget"].identity.state_ref
    environment_ref = phase4["environment"].identity.state_ref
    security_ref = phase4["security"].identity.state_ref

    source = ObservationSourceState(
        identity=identity(10),
        status=status(),
        source_ref=typed(11, "observation_source"),
        source_kind=ObservationSourceKind.TOOL_RESULT,
        source_status=ObservationSourceStatus.AVAILABLE,
        display_name="tool result projection",
        boundary_state_refs=(boundary_ref,),
        security_state_refs=(security_ref,),
        environment_state_refs=(environment_ref,),
        trust_level_label="trusted_by_boundary",
        reliability_label="reported",
        created_at_ref=typed(12, "time"),
        related_run_ref=run_ref,
        related_task_ref=task_ref,
        related_skill_ref=skill_ref,
        related_tool_group_ref=tool_group_ref,
        related_tool_intent_ref=tool_intent_ref,
        related_action_ref=action_ref,
        related_effect_ref=effect_ref,
    )
    channel = ObservationChannelState(
        identity=identity(20),
        status=status(),
        channel_ref=typed(21, "observation_channel"),
        channel_kind=ObservationChannelKind.EVENT_PROJECTION,
        channel_status=ObservationChannelStatus.OPEN,
        source_state_refs=(source.identity.state_ref,),
        boundary_state_refs=(boundary_ref,),
        resource_state_refs=(resource_ref,),
        security_state_refs=(security_ref,),
        expected_observation_kinds=("effect", "boundary"),
        visibility_scope_ref=typed(22, "scope"),
        latency_label="low",
        throughput_label="bounded",
        lossiness_label="none_reported",
        ordering_label="ordered_by_source",
    )
    frame = ObservationFrameState(
        identity=identity(30),
        status=status(),
        frame_ref=typed(31, "observation_frame"),
        frame_kind=ObservationFrameKind.EFFECT,
        frame_status=ObservationFrameStatus.ACCEPTED,
        source_state_ref=source.identity.state_ref,
        channel_state_ref=channel.identity.state_ref,
        observed_subject_ref=effect_ref,
        observed_subject_kind="effect_observation",
        observed_status="observation_pending",
        observed_summary="effect observation reference accepted",
        observed_payload_ref=typed(32, "redacted_payload_ref"),
        boundary_state_refs=(boundary_ref,),
        security_state_refs=(security_ref,),
        timestamp_ref=typed(33, "time"),
        related_run_ref=run_ref,
        related_task_ref=task_ref,
        related_skill_ref=skill_ref,
        related_tool_group_ref=tool_group_ref,
        related_tool_intent_ref=tool_intent_ref,
        related_action_ref=action_ref,
        related_effect_ref=effect_ref,
    )
    stream = EventStreamState(
        identity=identity(40),
        status=status(),
        stream_ref=typed(41, "event_stream"),
        stream_kind=EventStreamKind.RUN_EVENT_STREAM,
        stream_status=EventStreamStatus.STREAMING,
        source_state_refs=(source.identity.state_ref,),
        channel_state_refs=(channel.identity.state_ref,),
        latest_frame_ref=frame.identity.state_ref,
        frame_count=3,
        dropped_frame_count=1,
        redacted_frame_count=1,
        interruption_reason_ref=typed(42, "reason"),
        truncation_reason_ref=typed(43, "reason"),
        related_run_ref=run_ref,
        related_task_ref=task_ref,
    )
    quality = ObservationQualityState(
        identity=identity(50),
        status=status(),
        quality_ref=typed(51, "observation_quality"),
        quality_dimension=ObservationQualityDimension.COMPLETENESS,
        quality_status=ObservationQualityStatus.PARTIAL,
        quality_label="partial_but_usable_hint",
        quality_summary="external quality label says frame is partial",
        evidence_frame_refs=(frame.identity.state_ref,),
        boundary_state_refs=(boundary_ref,),
        security_state_refs=(security_ref,),
    )
    metric = ObservationMetricState(
        identity=identity(60),
        status=status(),
        metric_ref=typed(61, "observation_metric"),
        metric_kind=ObservationMetricKind.LATENCY,
        metric_status=ObservationMetricStatus.REPORTED,
        metric_name="observed_latency",
        metric_value_repr="42ms",
        metric_unit="ms",
        metric_window_ref=typed(62, "time_window"),
        source_state_ref=source.identity.state_ref,
        channel_state_ref=channel.identity.state_ref,
        related_resource_state_refs=(resource_ref,),
        related_run_ref=run_ref,
        related_task_ref=task_ref,
        quality_state_ref=quality.identity.state_ref,
    )
    audit = AuditObservationState(
        identity=identity(70),
        status=status(),
        audit_observation_ref=typed(71, "audit_observation"),
        audit_kind=AuditObservationKind.EFFECT_AUDIT,
        audit_status=AuditObservationStatus.LINKED,
        frame_state_refs=(frame.identity.state_ref,),
        event_stream_state_refs=(stream.identity.state_ref,),
        metric_state_refs=(metric.identity.state_ref,),
        related_run_ref=run_ref,
        related_task_ref=task_ref,
        related_skill_ref=skill_ref,
        related_tool_group_ref=tool_group_ref,
        related_tool_intent_ref=tool_intent_ref,
        related_action_ref=action_ref,
        related_effect_ref=effect_ref,
        related_boundary_state_refs=(boundary_ref,),
        related_security_state_refs=(security_ref,),
        audit_summary="audit observation linked to effect",
        audit_payload_ref=typed(72, "audit_payload_ref"),
    )
    projection = ObservationProjectionState(
        identity=identity(80),
        status=status(),
        projection_ref=typed(81, "observation_projection"),
        projection_kind=ObservationProjectionKind.RUN_OBSERVATION_PROJECTION,
        projection_status=ObservationProjectionStatus.PARTIAL,
        source_frame_refs=(frame.identity.state_ref,),
        source_stream_refs=(stream.identity.state_ref,),
        source_metric_refs=(metric.identity.state_ref,),
        source_audit_refs=(audit.identity.state_ref,),
        quality_state_refs=(quality.identity.state_ref,),
        projected_subject_ref=run_ref,
        projected_subject_kind="run",
        projected_status_summary="partial observation",
        projected_observation_summary="run observation remains partial and redacted",
        redaction_state_refs=(security_ref,),
        conflict_state_refs=(quality.identity.state_ref,),
    )
    return {
        "source": source,
        "channel": channel,
        "frame": frame,
        "stream": stream,
        "metric": metric,
        "audit": audit,
        "quality": quality,
        "projection": projection,
        "phase4": phase4,
        "model_feedback_ref": feedback_ref,
    }


def test_l2_phase5_cross_phase_chain_links_previous_stage_refs_only():
    objects = build_phase5_chain()
    phase4 = objects["phase4"]
    phase3 = phase4["phase3"]

    assert objects["source"].related_run_ref == phase3["run"].identity.state_ref
    assert objects["source"].related_tool_intent_ref == phase3["tool_intent"].identity.state_ref
    assert objects["frame"].related_effect_ref == phase3["effect_observation"].identity.state_ref
    assert objects["channel"].boundary_state_refs == (phase4["boundary_check"].identity.state_ref,)
    assert objects["metric"].related_resource_state_refs == (phase4["budget"].identity.state_ref,)
    assert objects["audit"].related_security_state_refs == (phase4["security"].identity.state_ref,)
    assert objects["projection"].quality_state_refs == (objects["quality"].identity.state_ref,)


def test_l2_phase5_objects_are_stably_serializable_and_hashable():
    for name, item in build_phase5_chain().items():
        if name in {"phase4", "model_feedback_ref"}:
            continue
        first = stable_json_dumps(item)
        second = stable_json_dumps(item)
        digest = stable_hash(item)
        assert first == second
        assert '"schema_version":"0.1"' in first
        assert len(digest) == 64


def test_l2_phase5_chain_uses_typed_refs_without_embedded_executors():
    objects = build_phase5_chain()
    checked_refs = (
        objects["source"].related_run_ref,
        objects["frame"].observed_subject_ref,
        objects["stream"].latest_frame_ref,
        objects["projection"].projected_subject_ref,
    )

    assert all(isinstance(item, TypedRef) for item in checked_refs)
    assert not hasattr(objects["frame"], "parser")
    assert not hasattr(objects["stream"], "event_bus")
