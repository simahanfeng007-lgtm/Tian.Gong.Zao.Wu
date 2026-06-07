"""Affective seven-emotion and six-desire signal vectors for L6 phase4.

Vectors are modulation hints only. They cannot permit, decide, dispatch models,
or dispatch tools.
"""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l6_plugins.common._common import L6_COMMON_SCHEMA_VERSION, ensure_bool, ensure_score, ensure_ref_text, ensure_schema_version, stable_digest


def _score(value: float, field_name: str) -> None:
    ensure_score(value, field_name)


@dataclass(frozen=True)
class SevenEmotionSignalVector:
    vector_ref: str = "projection:l6_phase4_seven_emotion_signal_vector"
    joy: float = 0.5
    anger: float = 0.0
    worry: float = 0.0
    thoughtfulness: float = 0.5
    sadness: float = 0.0
    fear: float = 0.0
    surprise: float = 0.0
    expression_only: bool = True
    permission_bypass: bool = False
    tool_dispatch: bool = False
    dispatches_model: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.vector_ref, "SevenEmotionSignalVector.vector_ref")
        for field_name in ("joy", "anger", "worry", "thoughtfulness", "sadness", "fear", "surprise"):
            _score(getattr(self, field_name), f"SevenEmotionSignalVector.{field_name}")
        for field_name in ("expression_only", "permission_bypass", "tool_dispatch", "dispatches_model"):
            ensure_bool(getattr(self, field_name), f"SevenEmotionSignalVector.{field_name}")
        if not self.expression_only or self.permission_bypass or self.tool_dispatch or self.dispatches_model:
            raise ValueError("seven emotion vector can only modulate expression")
        ensure_schema_version(self.schema_version)

    @property
    def intensity_score(self) -> float:
        return min(1.0, max(self.joy, self.anger, self.worry, self.thoughtfulness, self.sadness, self.fear, self.surprise))

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True)
class SixDesireTendencyVector:
    vector_ref: str = "projection:l6_phase4_six_desire_tendency_vector"
    survival: float = 0.5
    curiosity: float = 0.5
    achievement: float = 0.5
    connection: float = 0.5
    order: float = 0.5
    rest: float = 0.0
    candidate_ranking_only: bool = True
    action_dispatch: bool = False
    permission_bypass: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.vector_ref, "SixDesireTendencyVector.vector_ref")
        for field_name in ("survival", "curiosity", "achievement", "connection", "order", "rest"):
            _score(getattr(self, field_name), f"SixDesireTendencyVector.{field_name}")
        for field_name in ("candidate_ranking_only", "action_dispatch", "permission_bypass"):
            ensure_bool(getattr(self, field_name), f"SixDesireTendencyVector.{field_name}")
        if not self.candidate_ranking_only or self.action_dispatch or self.permission_bypass:
            raise ValueError("six desire vector can only modulate candidate ranking")
        ensure_schema_version(self.schema_version)

    @property
    def tendency_score(self) -> float:
        return min(1.0, (self.curiosity + self.achievement + self.connection + self.order + (1.0 - self.rest)) / 5.0)

    @property
    def digest(self) -> str:
        return stable_digest(self)
