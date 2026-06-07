"""模型计划器模式。"""

from __future__ import annotations

from enum import Enum


class PlannerMode(str, Enum):
    """自然语言到结构化计划的启用模式。"""

    RULE_ONLY = "rule_only"
    MODEL_SUGGEST = "model_suggest"
    MODEL_REQUIRED = "model_required"


def normalize_planner_mode(mode: str | PlannerMode | None) -> PlannerMode:
    if isinstance(mode, PlannerMode):
        return mode
    value = (mode or PlannerMode.RULE_ONLY.value).strip().lower().replace("-", "_")
    aliases = {
        "rule": PlannerMode.RULE_ONLY,
        "rule_only": PlannerMode.RULE_ONLY,
        "rules": PlannerMode.RULE_ONLY,
        "off": PlannerMode.RULE_ONLY,
        "disabled": PlannerMode.RULE_ONLY,
        "model": PlannerMode.MODEL_SUGGEST,
        "model_suggest": PlannerMode.MODEL_SUGGEST,
        "suggest": PlannerMode.MODEL_SUGGEST,
        "model_required": PlannerMode.MODEL_REQUIRED,
        "required": PlannerMode.MODEL_REQUIRED,
    }
    return aliases.get(value, PlannerMode.RULE_ONLY)
