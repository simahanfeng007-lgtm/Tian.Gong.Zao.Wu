"""L4 第一阶段 dry-run 与 no-op 动作落地替身。"""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .disabled import ExecutionDisabledByDefaultFailure
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true
from .request_intake import ActionRequestIntake
from .result import ActionGroundingResult, ActionGroundingResultKind


@dataclass(frozen=True, slots=True)
class DryRunActionGroundingRunner:
    """dry-run runner 只记录计划性结果，不执行真实动作。"""

    runner_ref: TypedRef
    l5_permit_ref: TypedRef | None = None
    produces_real_actions: bool = False
    runner_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_false(self.produces_real_actions, "DryRunActionGroundingRunner.produces_real_actions")
        ensure_true(self.runner_only, "DryRunActionGroundingRunner.runner_only")
        ensure_schema_version(self.schema_version, "DryRunActionGroundingRunner.schema_version")

    def run(self, intake: ActionRequestIntake, result_ref: TypedRef, failure_ref: TypedRef) -> ActionGroundingResult:
        permit_ref = intake.l5_permit_ref or self.l5_permit_ref
        if permit_ref is None:
            failure = ExecutionDisabledByDefaultFailure(failure_ref=failure_ref, source_request_ref=intake.source_request_ref).to_failure()
            return ActionGroundingResult(
                result_ref=result_ref,
                result_kind=ActionGroundingResultKind.REJECTED,
                source_request_ref=intake.source_request_ref,
                output_summary="dry-run runner refused because future L5 permit ref is missing",
                payload_items=(("runner", "dry_run"), ("real_action", "false")),
                failure=failure,
            )
        return ActionGroundingResult(
            result_ref=result_ref,
            result_kind=ActionGroundingResultKind.DRY_RUN,
            source_request_ref=intake.source_request_ref,
            output_summary="dry-run action grounding result only",
            payload_items=(("runner", "dry_run"), ("real_action", "false"), ("permit_ref_present", "true")),
        )


@dataclass(frozen=True, slots=True)
class NoOpActionGroundingRunner:
    """no-op runner 只返回空操作结果，不执行真实动作。"""

    runner_ref: TypedRef
    l5_permit_ref: TypedRef | None = None
    produces_real_actions: bool = False
    runner_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_false(self.produces_real_actions, "NoOpActionGroundingRunner.produces_real_actions")
        ensure_true(self.runner_only, "NoOpActionGroundingRunner.runner_only")
        ensure_schema_version(self.schema_version, "NoOpActionGroundingRunner.schema_version")

    def run(self, intake: ActionRequestIntake, result_ref: TypedRef, failure_ref: TypedRef) -> ActionGroundingResult:
        permit_ref = intake.l5_permit_ref or self.l5_permit_ref
        if permit_ref is None:
            failure = ExecutionDisabledByDefaultFailure(failure_ref=failure_ref, source_request_ref=intake.source_request_ref).to_failure()
            return ActionGroundingResult(
                result_ref=result_ref,
                result_kind=ActionGroundingResultKind.REJECTED,
                source_request_ref=intake.source_request_ref,
                output_summary="no-op runner refused because future L5 permit ref is missing",
                payload_items=(("runner", "no_op"), ("real_action", "false")),
                failure=failure,
            )
        return ActionGroundingResult(
            result_ref=result_ref,
            result_kind=ActionGroundingResultKind.NO_OP,
            source_request_ref=intake.source_request_ref,
            output_summary="no-op action grounding result only",
            payload_items=(("runner", "no_op"), ("real_action", "false"), ("permit_ref_present", "true")),
        )
