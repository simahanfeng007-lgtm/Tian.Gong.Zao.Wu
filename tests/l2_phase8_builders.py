from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l2_state import (
    AuditStateProjection,
    CompatibilityGateState,
    CompatibilityStatus,
    ComponentCompatibilityStatus,
    ComponentDependencyKind,
    ComponentStatus,
    DebugStateProjection,
    DeprecationState,
    HumanReadableStateProjection,
    L2ClosureStatus,
    L2ComponentDependencyState,
    L2ComponentHealthState,
    L2ComponentState,
    L2ExportState,
    L2FreezeState,
    L2HandoffState,
    L2IssueSeverity,
    L2IssueStatus,
    L2KnownIssueState,
    L2StateCatalog,
    L2StateDomain,
    L2StateIdentity,
    L2StateKind,
    L2StateStatus,
    L2StateStatusKind,
    L2ValidationSummaryState,
    L3HandoffProjection,
    LegacyMappingState,
    MigrationHintState,
    ModelVisibleStateProjection,
    ProjectionAudience,
    ProjectionFragmentState,
    ProjectionFreshness,
    ProjectionStatus,
    ProjectionVisibility,
    RuntimeSliceProjectionState,
    SchemaVersionState,
    StateDomainCatalog,
    StateObjectMeta,
)


def ref(prefix: str, index: int) -> RefId:
    return RefId(f"{prefix}:{index:032x}")


def typed(index: int, ref_type: str) -> TypedRef:
    return TypedRef(ref("phase8", index), ref_type)


def identity(index: int, kind: L2StateKind) -> L2StateIdentity:
    return L2StateIdentity(state_ref=typed(index, kind.value), kind=kind)


def status() -> L2StateStatus:
    return L2StateStatus(kind=L2StateStatusKind.DECLARED, reason="phase8 fixture")


def build_component_compatibility_objects():
    component_ref = typed(10, "component")
    target_ref = typed(11, "component")
    schema_ref = typed(12, "schema")
    mapping_ref = typed(13, "mapping")
    validation_ref = typed(14, "validation")
    return {
        "component": L2ComponentState(
            identity=identity(100, L2StateKind.COMPONENT),
            status=status(),
            component_id=component_ref,
            domain=L2StateDomain.PROJECTION_COMPATIBILITY_CLOSURE,
            module_ref=typed(15, "module"),
            version="0.1",
            public_exports=("L2ComponentState",),
            dependency_refs=(target_ref,),
            health_ref=typed(16, "health"),
            summary="phase8 component state fixture",
        ),
        "dependency": L2ComponentDependencyState(
            identity=identity(101, L2StateKind.COMPONENT),
            status=status(),
            dependency_id=typed(17, "dependency"),
            source_component_ref=component_ref,
            target_component_refs=(target_ref,),
            dependency_kind=ComponentDependencyKind.REFERENCE,
            compatibility_status=ComponentCompatibilityStatus.COMPATIBLE,
        ),
        "health": L2ComponentHealthState(
            identity=identity(102, L2StateKind.COMPONENT),
            status=status(),
            health_id=typed(18, "health"),
            component_refs=(component_ref,),
            import_status=ComponentStatus.AVAILABLE,
            serialization_status=ComponentStatus.AVAILABLE,
            hash_status=ComponentStatus.AVAILABLE,
            test_status=ComponentStatus.AVAILABLE,
            issue_count=0,
        ),
        "export": L2ExportState(
            identity=identity(103, L2StateKind.COMPONENT),
            status=status(),
            export_id=typed(19, "export"),
            module_ref=typed(15, "module"),
            exported_names=("L2ComponentState",),
            export_status=ComponentStatus.AVAILABLE,
        ),
        "schema_version": SchemaVersionState(
            identity=identity(110, L2StateKind.COMPATIBILITY),
            status=status(),
            schema_ref=schema_ref,
            version="0.1",
            domain=L2StateDomain.PROJECTION_COMPATIBILITY_CLOSURE,
            stable_hash="sha256:fixture",
            compatibility_status=CompatibilityStatus.COMPATIBLE,
        ),
        "legacy_mapping": LegacyMappingState(
            identity=identity(111, L2StateKind.COMPATIBILITY),
            status=status(),
            mapping_id=mapping_ref,
            legacy_ref=typed(20, "legacy_state"),
            new_ref=component_ref,
            mapping_status=CompatibilityStatus.COMPATIBLE_WITH_WARNING,
            confidence_hint=0.75,
            loss_risk="summary-only mapping",
        ),
        "deprecation": DeprecationState(
            identity=identity(112, L2StateKind.COMPATIBILITY),
            status=status(),
            deprecation_id=typed(21, "deprecation"),
            target_ref=typed(20, "legacy_state"),
            replacement_ref=component_ref,
            deprecation_status=CompatibilityStatus.DEPRECATED,
        ),
        "migration_hint": MigrationHintState(
            identity=identity(113, L2StateKind.COMPATIBILITY),
            status=status(),
            migration_hint_id=typed(22, "migration_hint"),
            source_schema_ref=typed(23, "legacy_schema"),
            target_schema_ref=schema_ref,
            required_steps_summary="record migration hint only",
            validation_need_hint="needs later validation",
            recovery_need_hint="needs later recovery reference",
        ),
        "compatibility_gate": CompatibilityGateState(
            identity=identity(114, L2StateKind.COMPATIBILITY),
            status=status(),
            gate_id=typed(24, "compatibility_gate"),
            target_refs=(component_ref,),
            schema_refs=(schema_ref,),
            mapping_refs=(mapping_ref,),
            validation_refs=(validation_ref,),
            gate_status=CompatibilityStatus.COMPATIBLE_WITH_WARNING,
        ),
    }


def build_projection_objects():
    run_ref = typed(30, "run")
    skill_ref = typed(31, "skill")
    tool_group_ref = typed(32, "tool_group")
    candidate_ref = typed(33, "candidate")
    validation_ref = typed(34, "validation")
    recovery_ref = typed(35, "recovery")
    fragment_ref = typed(36, "projection_fragment")
    return {
        "fragment": ProjectionFragmentState(
            identity=identity(200, L2StateKind.PROJECTION),
            status=status(),
            fragment_id=fragment_ref,
            source_state_refs=(run_ref, skill_ref),
            audience=ProjectionAudience.MODEL,
            visibility=ProjectionVisibility.SUMMARY_ONLY,
            title="phase8 projection fragment",
            summary="projection state fixture",
            content_hash="sha256:fragment",
            freshness=ProjectionFreshness.FRESH,
        ),
        "model_visible": ModelVisibleStateProjection(
            identity=identity(201, L2StateKind.PROJECTION),
            status=status(),
            projection_id=typed(37, "model_projection"),
            run_ref=run_ref,
            skill_refs=(skill_ref,),
            tool_group_refs=(tool_group_ref,),
            model_intent_refs=(typed(38, "model_intent"),),
            observation_refs=(typed(39, "observation"),),
            memory_context_refs=(typed(40, "context"),),
            candidate_refs=(candidate_ref,),
            validation_refs=(validation_ref,),
            recovery_refs=(recovery_ref,),
            visible_fragments=(fragment_ref,),
            hidden_reason_summary="restricted items remain hidden",
            projection_status=ProjectionStatus.READY,
        ),
        "human": HumanReadableStateProjection(
            identity=identity(202, L2StateKind.PROJECTION),
            status=status(),
            projection_id=typed(41, "human_projection"),
            title="L2 phase8 human projection",
            lifecycle_summary="state-only lifecycle summary",
            current_run_summary="state-only run summary",
            projection_status=ProjectionStatus.PARTIAL,
        ),
        "debug": DebugStateProjection(
            identity=identity(203, L2StateKind.PROJECTION),
            status=status(),
            projection_id=typed(42, "debug_projection"),
            component_refs=(typed(43, "component"),),
            dependency_refs=(typed(44, "dependency"),),
            test_result_refs=(typed(45, "test_result"),),
            projection_status=ProjectionStatus.READY,
        ),
        "audit": AuditStateProjection(
            identity=identity(204, L2StateKind.PROJECTION),
            status=status(),
            projection_id=typed(46, "audit_projection"),
            audit_refs=(typed(47, "audit"),),
            boundary_refs=(typed(48, "boundary"),),
            decision_refs=(typed(49, "decision"),),
            validation_refs=(validation_ref,),
            immutable_summary_hash="sha256:audit-summary",
            projection_status=ProjectionStatus.READY,
        ),
        "l3_handoff": L3HandoffProjection(
            identity=identity(205, L2StateKind.PROJECTION),
            status=status(),
            projection_id=typed(50, "l3_handoff_projection"),
            l2_version="0.1",
            stable_state_domains=(L2StateDomain.BASE.value, L2StateDomain.PROJECTION_COMPATIBILITY_CLOSURE.value),
            public_state_refs=(skill_ref, tool_group_ref),
            boundary_refs=(typed(48, "boundary"),),
            unsupported_items=("real scheduler",),
            l3_allowed_usage_summary="L3 may reference immutable state facts",
            l3_forbidden_usage_summary="L3 must not treat L2 projection as execution authority",
            projection_status=ProjectionStatus.READY,
        ),
        "runtime_slice": RuntimeSliceProjectionState(
            identity=identity(206, L2StateKind.PROJECTION),
            status=status(),
            slice_id=typed(51, "runtime_slice"),
            run_ref=run_ref,
            task_ref=typed(52, "task"),
            goal_ref=typed(53, "goal"),
            skill_ref=skill_ref,
            tool_group_ref=tool_group_ref,
            model_intent_ref=typed(38, "model_intent"),
            observation_ref=typed(39, "observation"),
            context_ref=typed(40, "context"),
            candidate_ref=candidate_ref,
            validation_ref=validation_ref,
            recovery_ref=recovery_ref,
            projection_refs=(fragment_ref,),
            projection_status=ProjectionStatus.READY,
        ),
    }


def build_catalog_closure_objects():
    object_meta = StateObjectMeta(
        identity=identity(300, L2StateKind.CATALOG),
        status=status(),
        object_name="L2ComponentState",
        module_ref=typed(60, "module"),
        domain=L2StateDomain.PROJECTION_COMPATIBILITY_CLOSURE,
        phase="phase8",
        version="0.1",
        summary="component state meta",
    )
    domain_catalog = StateDomainCatalog(
        identity=identity(301, L2StateKind.CATALOG),
        status=status(),
        catalog_id=typed(61, "domain_catalog"),
        domain=L2StateDomain.PROJECTION_COMPATIBILITY_CLOSURE,
        state_objects=(object_meta,),
        dependency_domains=(L2StateDomain.BASE,),
        export_refs=(typed(62, "export"),),
        summary="phase8 domain catalog",
    )
    state_catalog = L2StateCatalog(
        identity=identity(302, L2StateKind.CATALOG),
        status=status(),
        catalog_id=typed(63, "l2_catalog"),
        l2_version="0.1",
        domains=(domain_catalog,),
        total_object_count=1,
        public_object_count=1,
        deprecated_object_count=0,
        compatibility_refs=(typed(64, "compatibility"),),
    )
    validation_summary = L2ValidationSummaryState(
        identity=identity(310, L2StateKind.CLOSURE),
        status=status(),
        summary_id=typed(65, "validation_summary"),
        compileall_status="passed",
        pytest_status="passed",
        serialization_status="passed",
        hash_status="passed",
        import_status="passed",
        boundary_status="passed",
        passed_count=459,
        failed_count=0,
        warning_count=0,
    )
    issue = L2KnownIssueState(
        identity=identity(311, L2StateKind.CLOSURE),
        status=status(),
        issue_id=typed(66, "known_issue"),
        severity=L2IssueSeverity.INFO,
        affected_refs=(typed(67, "future_layer"),),
        summary="L3 orchestration remains future work",
        workaround_summary="keep L2 as state-only baseline",
        target_followup_layer="L3",
        issue_status=L2IssueStatus.RECORDED,
    )
    handoff = L2HandoffState(
        identity=identity(312, L2StateKind.CLOSURE),
        status=status(),
        handoff_id=typed(68, "handoff"),
        l2_version="0.1",
        frozen_refs=(typed(69, "freeze"),),
        l3_entry_refs=(typed(70, "l3_entry"),),
        l3_allowed_usage_summary="reference L2 immutable state objects",
        l3_forbidden_usage_summary="do not use L2 as scheduler or executor",
        known_issue_refs=(typed(66, "known_issue"),),
        validation_summary_ref=typed(65, "validation_summary"),
        closure_status=L2ClosureStatus.READY_FOR_FREEZE,
    )
    freeze = L2FreezeState(
        identity=identity(313, L2StateKind.CLOSURE),
        status=status(),
        freeze_id=typed(69, "freeze"),
        l2_version="0.1",
        source_archive_ref=typed(71, "archive"),
        manifest_hash="sha256:manifest",
        validation_summary_ref=typed(65, "validation_summary"),
        handoff_ref=typed(68, "handoff"),
        freeze_status=L2ClosureStatus.READY_FOR_FREEZE,
        reason_summary="phase8 closure state fixture",
    )
    return {
        "object_meta": object_meta,
        "domain_catalog": domain_catalog,
        "state_catalog": state_catalog,
        "validation_summary": validation_summary,
        "known_issue": issue,
        "handoff": handoff,
        "freeze": freeze,
    }


def build_all_phase8_objects():
    result = {}
    result.update(build_component_compatibility_objects())
    result.update(build_projection_objects())
    result.update(build_catalog_closure_objects())
    return result
