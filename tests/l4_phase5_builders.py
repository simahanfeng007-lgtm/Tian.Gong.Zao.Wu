from l3_phase1_builders import typed
from tiangong_kernel.l4_action_grounding import (
    DesktopActionEnvelope,
    DesktopActionRequest,
    ExternalActionRiskSurface,
    ExternalActionScope,
    ExternalActionSurface,
    FileActionEnvelope,
    FileActionRequest,
    NetworkActionEnvelope,
    NetworkActionRequest,
    ReversibilityDescriptor,
    ReversibilityKind,
    ResourceUsageDescriptor,
    SideEffectDescriptor,
    SideEffectKind,
    TerminalActionEnvelope,
    TerminalActionRequest,
)


def phase5_ref(offset: int, ref_type: str):
    return typed(8000 + offset, ref_type)


def side_effect(*effects: SideEffectKind, summary="phase5_descriptor"):
    return SideEffectDescriptor(
        side_effect_ref=phase5_ref(1, "side_effect"),
        effect_kinds=effects,
        summary=summary,
    )


def reversibility(kind=ReversibilityKind.UNKNOWN):
    return ReversibilityDescriptor(
        reversibility_ref=phase5_ref(2, "reversibility"),
        reversibility_kind=kind,
        summary=kind.value,
    )


def resource_usage(summary="dry_run_preview_only"):
    return ResourceUsageDescriptor(
        resource_usage_ref=phase5_ref(3, "resource_usage"),
        summary=summary,
        usage_items=(("mode", "preview"),),
    )


def risk(surface: ExternalActionSurface):
    return ExternalActionRiskSurface(
        risk_surface_ref=phase5_ref(4, "external_risk_surface"),
        summary=f"{surface.value}_risk_surface",
        filesystem=surface is ExternalActionSurface.FILESYSTEM,
        network=surface is ExternalActionSurface.NETWORK,
        terminal=surface is ExternalActionSurface.TERMINAL,
        desktop=surface is ExternalActionSurface.DESKTOP,
    )


def scope(surface: ExternalActionSurface):
    return ExternalActionScope(
        scope_ref=phase5_ref(5, "external_scope"),
        surface=surface,
        path_scope_ref=phase5_ref(6, "path_scope") if surface is ExternalActionSurface.FILESYSTEM else None,
        domain_scope_ref=phase5_ref(7, "domain_scope") if surface is ExternalActionSurface.NETWORK else None,
        command_scope_ref=phase5_ref(8, "command_scope") if surface is ExternalActionSurface.TERMINAL else None,
        desktop_scope_ref=phase5_ref(9, "desktop_scope") if surface is ExternalActionSurface.DESKTOP else None,
        scope_items=(("surface", surface.value),),
    )


def file_request():
    request_ref = phase5_ref(10, "file_action_request")
    external_scope = scope(ExternalActionSurface.FILESYSTEM)
    effect = side_effect(SideEffectKind.READ_ONLY, summary="file_preview_only")
    reverse = reversibility(ReversibilityKind.UNKNOWN)
    usage = resource_usage("file_preview_usage")
    risk_surface = risk(ExternalActionSurface.FILESYSTEM)
    envelope = FileActionEnvelope(
        envelope_ref=phase5_ref(11, "file_action_envelope"),
        request_ref=request_ref,
        scope=external_scope,
        side_effect=effect,
        reversibility=reverse,
        resource_usage=usage,
        risk_surface=risk_surface,
    )
    return FileActionRequest(
        request_ref=request_ref,
        path_intent_ref=phase5_ref(12, "path_intent"),
        operation_ref=phase5_ref(13, "file_operation"),
        action_envelope=envelope,
        scope=external_scope,
        side_effect=effect,
        reversibility=reverse,
        resource_usage=usage,
        risk_surface=risk_surface,
        l3_action_intent_ref=phase5_ref(14, "action_intent"),
        l3_tool_intent_ref=phase5_ref(15, "tool_intent"),
    )


def network_request():
    request_ref = phase5_ref(20, "network_action_request")
    external_scope = scope(ExternalActionSurface.NETWORK)
    effect = side_effect(SideEffectKind.NETWORK_SEND, summary="network_preview_only")
    reverse = reversibility(ReversibilityKind.UNKNOWN)
    usage = resource_usage("network_preview_usage")
    risk_surface = risk(ExternalActionSurface.NETWORK)
    envelope = NetworkActionEnvelope(
        envelope_ref=phase5_ref(21, "network_action_envelope"),
        request_ref=request_ref,
        scope=external_scope,
        side_effect=effect,
        reversibility=reverse,
        resource_usage=usage,
        risk_surface=risk_surface,
    )
    return NetworkActionRequest(
        request_ref=request_ref,
        url_ref=phase5_ref(22, "url"),
        method_ref=phase5_ref(23, "method"),
        payload_ref=phase5_ref(24, "payload"),
        headers_ref=phase5_ref(25, "headers"),
        action_envelope=envelope,
        scope=external_scope,
        side_effect=effect,
        reversibility=reverse,
        resource_usage=usage,
        risk_surface=risk_surface,
        l3_action_intent_ref=phase5_ref(14, "action_intent"),
        l3_tool_intent_ref=phase5_ref(15, "tool_intent"),
    )


def terminal_request():
    request_ref = phase5_ref(30, "terminal_action_request")
    external_scope = scope(ExternalActionSurface.TERMINAL)
    effect = side_effect(SideEffectKind.PROCESS_SPAWN, summary="terminal_preview_only")
    reverse = reversibility(ReversibilityKind.IRREVERSIBLE)
    usage = resource_usage("terminal_preview_usage")
    risk_surface = risk(ExternalActionSurface.TERMINAL)
    envelope = TerminalActionEnvelope(
        envelope_ref=phase5_ref(31, "terminal_action_envelope"),
        request_ref=request_ref,
        scope=external_scope,
        side_effect=effect,
        reversibility=reverse,
        resource_usage=usage,
        risk_surface=risk_surface,
    )
    return TerminalActionRequest(
        request_ref=request_ref,
        command_ref=phase5_ref(32, "command"),
        args_ref=phase5_ref(33, "args"),
        working_dir_ref=phase5_ref(34, "working_dir"),
        env_ref=phase5_ref(35, "env"),
        action_envelope=envelope,
        scope=external_scope,
        side_effect=effect,
        reversibility=reverse,
        resource_usage=usage,
        risk_surface=risk_surface,
        l3_action_intent_ref=phase5_ref(14, "action_intent"),
        l3_tool_intent_ref=phase5_ref(15, "tool_intent"),
    )


def desktop_request():
    request_ref = phase5_ref(40, "desktop_action_request")
    external_scope = scope(ExternalActionSurface.DESKTOP)
    effect = side_effect(SideEffectKind.UI_INPUT, summary="desktop_preview_only")
    reverse = reversibility(ReversibilityKind.UNKNOWN)
    usage = resource_usage("desktop_preview_usage")
    risk_surface = risk(ExternalActionSurface.DESKTOP)
    envelope = DesktopActionEnvelope(
        envelope_ref=phase5_ref(41, "desktop_action_envelope"),
        request_ref=request_ref,
        scope=external_scope,
        side_effect=effect,
        reversibility=reverse,
        resource_usage=usage,
        risk_surface=risk_surface,
    )
    return DesktopActionRequest(
        request_ref=request_ref,
        ui_target_ref=phase5_ref(42, "ui_target"),
        gesture_ref=phase5_ref(43, "gesture"),
        screen_region_ref=phase5_ref(44, "screen_region"),
        input_ref=phase5_ref(45, "input"),
        action_envelope=envelope,
        scope=external_scope,
        side_effect=effect,
        reversibility=reverse,
        resource_usage=usage,
        risk_surface=risk_surface,
        l3_action_intent_ref=phase5_ref(14, "action_intent"),
        l3_tool_intent_ref=phase5_ref(15, "tool_intent"),
    )
