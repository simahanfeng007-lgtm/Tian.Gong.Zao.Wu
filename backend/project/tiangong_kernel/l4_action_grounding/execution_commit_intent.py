"""Commit intent references for L4 phase 7."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExecutionCommitIntent:
    """Commit intent only; it is not a commit command."""

    commit_intent_ref: TypedRef
    transaction_ref: TypedRef
    action_ref: TypedRef | None = None
    intent_summary: str = "commit_intent_ref_only"
    intent_only: bool = True
    executes_commit: bool = False
    writes_l2_state: bool = False
    grants_commit_permission: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.intent_summary, "ExecutionCommitIntent.intent_summary")
        ensure_true(self.intent_only, "ExecutionCommitIntent.intent_only")
        ensure_false(self.executes_commit, "ExecutionCommitIntent.executes_commit")
        ensure_false(self.writes_l2_state, "ExecutionCommitIntent.writes_l2_state")
        ensure_false(self.grants_commit_permission, "ExecutionCommitIntent.grants_commit_permission")
        ensure_schema_version(self.schema_version, "ExecutionCommitIntent.schema_version")
