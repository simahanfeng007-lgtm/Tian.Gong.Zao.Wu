"""L6 phase3 mind plugin group common declarations.

The mind layer is a candidate/projection/suggestion layer only. It is not a
runtime, not a scheduler, not a model client, not a tool invoker, and not a
state writer. All fields are summary/ref/digest oriented so the objects can be
handed to L3/L5/L2 through existing governance paths without causing effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l6_plugins.common._common import (
    L6_COMMON_SCHEMA_VERSION,
    ensure_bool,
    ensure_no_live_or_sensitive_text,
    ensure_ref_items,
    ensure_ref_text,
    ensure_schema_version,
    stable_digest,
)

L6_PHASE3 = "L6_PHASE3_MIND_STATE_PLUGIN_GROUP"


class MindPluginKind(str, Enum):
    CONTEXT = "context_mind"
    BELIEF = "belief_mind"
    WORLD_CONSTRAINT = "world_constraint_mind"
    GOAL = "goal_mind"
    INTENTION = "intention_mind"
    ATTENTION = "attention_mind"
    PREFERENCE = "preference_mind"
    AFFECTIVE = "affective_mind"
    MEMORY_CANDIDATE = "memory_candidate_mind"
    FORGETTING_CANDIDATE = "forgetting_candidate_mind"
    SELF_REFLECTION = "self_reflection_mind"
    LEARNING_EVOLUTION = "learning_evolution_mind"
    FUSION_SCORING = "mind_fusion_scoring"


class MindOutputKind(str, Enum):
    PROJECTION = "projection"
    REQUIREMENT = "requirement"
    SUGGESTION = "suggestion"
    EVENT = "event"
    HANDOFF = "handoff"
    REPORT = "report"
    SCORE = "score"


class MindCollaborationChannel(str, Enum):
    EVENT = "event"
    STATE_PROJECTION = "state_projection"
    HANDOFF = "handoff"
    PUBLIC_PROJECTION = "public_projection"
    HOST_MEDIATED_INVOCATION = "host_mediated_invocation"
    L3_L5_RESCHEDULE = "l3_l5_reschedule"


class GovernanceRefusalReason(str, Enum):
    SAFETY_POLICY = "safety_policy"
    PERMISSION_GOVERNANCE = "permission_governance"
    BUDGET_EXHAUSTED = "budget_exhausted"
    TOOL_UNAVAILABLE = "tool_unavailable"
    CONTEXT_INSUFFICIENT = "context_insufficient"
    USER_REQUIREMENT_UNCLEAR = "user_requirement_unclear"
    SYSTEM_BOUNDARY_BLOCKED = "system_boundary_blocked"


@dataclass(frozen=True)
class MindPluginDeclaration:
    plugin_ref: str
    plugin_kind: MindPluginKind | str
    summary: str
    input_summary_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_mind_input",))
    output_kind_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_mind_output",))
    event_refs: tuple[str, ...] = field(default_factory=tuple)
    handoff_refs: tuple[str, ...] = field(default_factory=tuple)
    quality_refs: tuple[str, ...] = field(default_factory=lambda: ("quality:l6_phase3_mind",))
    is_runtime: bool = False
    schedules_tasks: bool = False
    calls_model: bool = False
    calls_tool: bool = False
    writes_l2_fact: bool = False
    writes_memory: bool = False
    writes_audit: bool = False
    charges_budget: bool = False
    reads_credential: bool = False
    direct_plugin_link: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.plugin_ref, "MindPluginDeclaration.plugin_ref")
        object.__setattr__(self, "plugin_kind", MindPluginKind(self.plugin_kind))
        ensure_no_live_or_sensitive_text(self.summary, "MindPluginDeclaration.summary")
        for field_name in ("input_summary_refs", "output_kind_refs", "event_refs", "handoff_refs", "quality_refs"):
            ensure_ref_items(getattr(self, field_name), f"MindPluginDeclaration.{field_name}")
        for field_name in (
            "is_runtime", "schedules_tasks", "calls_model", "calls_tool", "writes_l2_fact", "writes_memory",
            "writes_audit", "charges_budget", "reads_credential", "direct_plugin_link",
        ):
            ensure_bool(getattr(self, field_name), f"MindPluginDeclaration.{field_name}")
        if any(
            (
                self.is_runtime,
                self.schedules_tasks,
                self.calls_model,
                self.calls_tool,
                self.writes_l2_fact,
                self.writes_memory,
                self.writes_audit,
                self.charges_budget,
                self.reads_credential,
                self.direct_plugin_link,
            )
        ):
            raise ValueError("L6 mind plugin declaration must remain inert and host-mediated")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True)
class MindPluginGroupArchitecture:
    group_ref: str = "mind:l6_phase3_group"
    phase: str = L6_PHASE3
    plugin_refs: tuple[str, ...] = field(default_factory=lambda: tuple(f"mind:{kind.value}" for kind in MindPluginKind))
    llm_is_primary_reasoner: bool = True
    l3_is_orchestration_owner: bool = True
    l4_is_action_grounding_owner: bool = True
    l5_is_governance_owner: bool = True
    l6_mind_is_auxiliary: bool = True
    creates_parallel_runtime: bool = False
    grants_permission: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.group_ref, "MindPluginGroupArchitecture.group_ref")
        if self.phase != L6_PHASE3:
            raise ValueError("MindPluginGroupArchitecture.phase must be L6 phase3")
        ensure_ref_items(self.plugin_refs, "MindPluginGroupArchitecture.plugin_refs", required=True)
        for field_name in (
            "llm_is_primary_reasoner", "l3_is_orchestration_owner", "l4_is_action_grounding_owner",
            "l5_is_governance_owner", "l6_mind_is_auxiliary", "creates_parallel_runtime", "grants_permission",
        ):
            ensure_bool(getattr(self, field_name), f"MindPluginGroupArchitecture.{field_name}")
        if not all((self.llm_is_primary_reasoner, self.l3_is_orchestration_owner, self.l4_is_action_grounding_owner, self.l5_is_governance_owner, self.l6_mind_is_auxiliary)):
            raise ValueError("L6 mind group must preserve LLM/L3/L4/L5 ownership")
        if self.creates_parallel_runtime or self.grants_permission:
            raise ValueError("L6 mind group cannot create runtime or grant permission")
        ensure_schema_version(self.schema_version)

    @property
    def mind_plugin_is_not_runtime(self) -> bool:
        return not self.creates_parallel_runtime and self.l6_mind_is_auxiliary


def default_mind_plugin_declarations() -> tuple[MindPluginDeclaration, ...]:
    summaries = {
        MindPluginKind.CONTEXT: "上下文摘要、断裂检测和安全投影候选。",
        MindPluginKind.BELIEF: "信念候选、置信度、冲突与污染风险投影。",
        MindPluginKind.WORLD_CONSTRAINT: "世界约束、规则边界和事实候选投影。",
        MindPluginKind.GOAL: "目标候选、优先级评分和任务级别建议。",
        MindPluginKind.INTENTION: "意图候选、计划候选和下一步建议。",
        MindPluginKind.ATTENTION: "注意力焦点、风险焦点和缺口焦点建议。",
        MindPluginKind.PREFERENCE: "偏好、价值取向和工作方式倾向摘要。",
        MindPluginKind.AFFECTIVE: "七情六欲、疲劳、压力与人格化表达建议。",
        MindPluginKind.MEMORY_CANDIDATE: "记忆召回、晋升、关联与安全过滤候选。",
        MindPluginKind.FORGETTING_CANDIDATE: "遗忘、衰减、污染隔离和冗余压缩候选。",
        MindPluginKind.SELF_REFLECTION: "质量自省、失败归因和缺口报告。",
        MindPluginKind.LEARNING_EVOLUTION: "学习需求、修复、迭代、迁移和热切换就绪候选。",
        MindPluginKind.FUSION_SCORING: "心智评分聚合、冲突分数和可解释摘要。",
    }
    return tuple(
        MindPluginDeclaration(
            plugin_ref=f"mind:{kind.value}",
            plugin_kind=kind,
            summary=summaries[kind],
            output_kind_refs=("projection:l6_mind", "suggestion:l6_mind", "score:l6_mind"),
        )
        for kind in MindPluginKind
    )
