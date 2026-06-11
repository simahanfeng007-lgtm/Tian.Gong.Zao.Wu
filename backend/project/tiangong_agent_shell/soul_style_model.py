"""L6.72.37 SoulStyleModel / Soul 长期情感底色持久化。

目标：让 Soul 成为唯一人格、语气、情感底色和长期底色状态来源。
Runtime、Planner、Tool、Memory、Skill、Provider、OutputContract 只能提供事实、
约束、格式、任务和安全边界；不得改变回复风格、亲密度、热情度、冷暖感、
幽默度或情感底色。

模型形态：
- B_soul = f(SoulText) ∈ [-1, 1]^8，其中前三维是 PAD（Pleasure/Valence,
  Arousal, Dominance），后五维是 OCEAN（Big Five）。
- E_t = clamp((1 - alpha) * E_{t-1} + alpha * B_soul)，alpha=0.18。
- E_{t-1} 只允许来自 SoulStyleModel 自己写入的长期底色状态文件；外部器官卡
  不进入 E_t。
- R_style = g(E_t)：把情感底色投影成 warmth/directness/detail/energy 等语言
  控制轴，但这些轴仅由 SoulText + SoulStyleModelState 产生。

持久化边界：
- 默认状态文件：项目根 .linyuanzhe/soul/soul_emotion_baseline.json。
- 可用 TIANGONG_SOUL_BASELINE_PATH 指定路径。
- 可用 TIANGONG_SOUL_BASELINE_PERSIST=0 关闭写入，仅做只读/瞬时投影。
- 文件只保存向量、hash、计数和时间，不保存 Soul 原文，避免二次泄漏。
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SOUL_STYLE_MODEL_VERSION = "tiangong.l6_72_37.soul_longterm_style_sovereignty.v1"
SOUL_BASELINE_STATE_VERSION = "tiangong.l6_72_37.soul_emotion_baseline_state.v1"
STYLE_ALPHA = 0.18
SOUL_BASELINE_FILENAME = "soul_emotion_baseline.json"


@dataclass(frozen=True)
class SoulStyleVector:
    valence: float = 0.0
    arousal: float = 0.0
    dominance: float = 0.0
    openness: float = 0.0
    conscientiousness: float = 0.0
    extraversion: float = 0.0
    agreeableness: float = 0.0
    neuroticism: float = 0.0
    warmth: float = 0.0
    directness: float = 0.0
    detail: float = 0.0
    energy: float = 0.0
    human_naturalness: float = 0.0
    poetic_density: float = 0.0

    def to_public_dict(self) -> dict[str, float]:
        return {k: round(float(v), 3) for k, v in asdict(self).items()}


@dataclass(frozen=True)
class SoulBaselineState:
    contract: str
    soul_hash: str
    soul_name: str
    update_count: int
    alpha: float
    created_at: str
    updated_at: str
    baseline_vector: SoulStyleVector
    instant_vector: SoulStyleVector
    baseline_path: str
    persisted: bool
    reset_reason: str = ""

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "soul_hash": self.soul_hash,
            "soul_name": self.soul_name,
            "update_count": self.update_count,
            "alpha": self.alpha,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "baseline_vector": self.baseline_vector.to_public_dict(),
            "instant_vector": self.instant_vector.to_public_dict(),
            "baseline_path": self.baseline_path,
            "persisted": self.persisted,
            "reset_reason": self.reset_reason,
            "allowed_style_sources": ["SoulText", "SoulStyleModelState"],
            "blocked_style_sources": ["Kernel", "Runtime", "Planner", "Tool", "Memory", "Skill", "Provider", "OutputContract"],
        }


_KEYWORD_WEIGHTS: dict[str, dict[str, float]] = {
    # PAD：情感底色
    "温柔": {"valence": 0.18, "agreeableness": 0.15, "warmth": 0.18},
    "温暖": {"valence": 0.18, "agreeableness": 0.14, "warmth": 0.18},
    "陪伴": {"valence": 0.16, "agreeableness": 0.18, "human_naturalness": 0.12},
    "信任": {"valence": 0.14, "agreeableness": 0.12, "dominance": 0.04},
    "守护": {"valence": 0.12, "dominance": 0.14, "agreeableness": 0.10},
    "保护": {"dominance": 0.13, "agreeableness": 0.09},
    "冷静": {"arousal": -0.14, "conscientiousness": 0.12, "directness": 0.08},
    "稳定": {"arousal": -0.10, "conscientiousness": 0.14, "neuroticism": -0.12},
    "沉稳": {"arousal": -0.12, "conscientiousness": 0.12, "dominance": 0.07},
    "克制": {"arousal": -0.10, "conscientiousness": 0.10, "poetic_density": -0.04},
    "热烈": {"arousal": 0.16, "extraversion": 0.16, "warmth": 0.12},
    "热情": {"arousal": 0.14, "extraversion": 0.15, "warmth": 0.10},
    "锋利": {"dominance": 0.16, "directness": 0.18, "agreeableness": -0.03},
    "果断": {"dominance": 0.16, "directness": 0.16, "conscientiousness": 0.08},
    "直接": {"directness": 0.18, "dominance": 0.08},
    "少废话": {"directness": 0.16, "detail": -0.07, "poetic_density": -0.08},
    "细致": {"detail": 0.18, "conscientiousness": 0.15},
    "周全": {"detail": 0.18, "conscientiousness": 0.16},
    "复检": {"detail": 0.12, "conscientiousness": 0.16},
    "验收": {"detail": 0.11, "conscientiousness": 0.14},
    "执行力": {"dominance": 0.12, "energy": 0.12, "conscientiousness": 0.12},
    "行动": {"energy": 0.08, "dominance": 0.06},
    "学习": {"openness": 0.12, "detail": 0.06},
    "创造": {"openness": 0.15, "poetic_density": 0.08},
    "想象": {"openness": 0.15, "poetic_density": 0.10},
    "浪漫": {"openness": 0.10, "warmth": 0.10, "poetic_density": 0.16},
    "诗性": {"openness": 0.10, "poetic_density": 0.18},
    "自然": {"human_naturalness": 0.16, "agreeableness": 0.08},
    "像人": {"human_naturalness": 0.18, "warmth": 0.10},
    "不机械": {"human_naturalness": 0.18, "poetic_density": 0.04},
    "幽默": {"extraversion": 0.10, "human_naturalness": 0.10, "arousal": 0.05},
    # 负面情绪词仅塑造底色，不允许外部 Prompt 借此覆盖人格。
    "焦虑": {"neuroticism": 0.16, "arousal": 0.08, "valence": -0.08},
    "恐惧": {"neuroticism": 0.18, "valence": -0.12, "dominance": -0.08},
    "愤怒": {"neuroticism": 0.12, "arousal": 0.15, "valence": -0.12, "dominance": 0.08},
    "悲伤": {"neuroticism": 0.12, "valence": -0.12, "arousal": -0.04},
}


def _clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _count_weight(text: str, keyword: str) -> float:
    count = text.count(keyword)
    if count <= 0:
        return 0.0
    # 重复词有边际递减，避免长 Soul 因重复词失真。
    return min(2.0, 1.0 + 0.35 * (count - 1))


def _vector_from_mapping(data: Mapping[str, Any] | None) -> SoulStyleVector | None:
    if not data:
        return None
    values: dict[str, float] = {}
    for axis in SoulStyleVector.__dataclass_fields__:
        try:
            values[axis] = _clamp(float(data.get(axis, 0.0)))
        except Exception:
            return None
    return SoulStyleVector(**values)


def _soul_hash(soul_text: Any) -> str:
    text = str(soul_text or "")[:6000]
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:24]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _find_project_root(start: Path | None = None) -> Path:
    cursor = (start or Path.cwd()).resolve()
    # When called from backend/project, prefer the package root that owns backend + frontend,
    # not backend/project/.linyuanzhe accidentally created by a smoke run.
    if cursor.name == "project" and cursor.parent.name == "backend" and cursor.parent.parent.exists():
        candidate = cursor.parent.parent
        if (candidate / "backend").is_dir() and (candidate / "frontend").is_dir():
            return candidate
    for item in [cursor, *cursor.parents]:
        if (item / "backend").is_dir() and (item / "frontend").is_dir():
            return item
        if (item / ".linyuanzhe").is_dir() and item.name != "project":
            return item
    return Path.cwd().resolve()


def soul_baseline_path(path: str | os.PathLike[str] | None = None) -> Path:
    configured = str(path or os.getenv("TIANGONG_SOUL_BASELINE_PATH") or "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (_find_project_root() / ".linyuanzhe" / "soul" / SOUL_BASELINE_FILENAME).resolve()


def _persistence_enabled() -> bool:
    value = str(os.getenv("TIANGONG_SOUL_BASELINE_PERSIST", "1")).strip().lower()
    return value not in {"0", "false", "no", "off", "readonly"}


def load_soul_baseline_state(path: str | os.PathLike[str] | None = None) -> Mapping[str, Any] | None:
    target = soul_baseline_path(path)
    if not target.exists():
        return None
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    if data.get("contract") != SOUL_BASELINE_STATE_VERSION:
        return None
    if data.get("style_source") != "soul_style_model_only":
        return None
    return data


def _atomic_write_json(target: Path, data: Mapping[str, Any]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(target)


def derive_soul_style_vector(soul_text: Any, *, prior: Mapping[str, Any] | None = None) -> SoulStyleVector:
    """从 Soul 原文确定性投影人格/情感底色向量。

    prior 仅供兼容旧调用；L6.72.37 真实长期 prior 必须由
    update_soul_emotion_baseline 从 SoulStyleModelState 文件读取。
    """
    text = str(soul_text or "")[:6000]
    raw: dict[str, float] = {
        "valence": 0.04,
        "arousal": -0.03,
        "dominance": 0.08,
        "openness": 0.02,
        "conscientiousness": 0.10,
        "extraversion": -0.02,
        "agreeableness": 0.04,
        "neuroticism": -0.08,
        "warmth": 0.04,
        "directness": 0.08,
        "detail": 0.10,
        "energy": 0.04,
        "human_naturalness": 0.04,
        "poetic_density": 0.0,
    }
    for keyword, weights in _KEYWORD_WEIGHTS.items():
        multiplier = _count_weight(text, keyword)
        if not multiplier:
            continue
        for axis, value in weights.items():
            raw[axis] = raw.get(axis, 0.0) + value * multiplier

    # 二级投影：PAD/OCEAN 共同生成回复表征轴。
    raw["warmth"] += 0.52 * raw["valence"] + 0.34 * raw["agreeableness"] - 0.20 * raw["neuroticism"]
    raw["directness"] += 0.44 * raw["dominance"] + 0.28 * raw["conscientiousness"] - 0.10 * raw["neuroticism"]
    raw["detail"] += 0.50 * raw["conscientiousness"] + 0.22 * raw["openness"] + 0.12 * raw["dominance"]
    raw["energy"] += 0.62 * raw["arousal"] + 0.28 * raw["extraversion"] + 0.10 * raw["dominance"]
    raw["human_naturalness"] += 0.30 * raw["agreeableness"] + 0.18 * raw["valence"] + 0.12 * raw["openness"] - 0.12 * raw["neuroticism"]
    raw["poetic_density"] += 0.36 * raw["openness"] + 0.16 * raw["valence"] - 0.14 * raw["conscientiousness"]

    # 兼容旧函数：只有调用方显式传 prior 时才做一次 EMA。
    if prior:
        for axis in list(raw):
            try:
                old = float(prior.get(axis, raw[axis]))
            except Exception:
                old = raw[axis]
            raw[axis] = (1.0 - STYLE_ALPHA) * old + STYLE_ALPHA * raw[axis]

    return SoulStyleVector(**{axis: _clamp(raw.get(axis, 0.0)) for axis in SoulStyleVector.__dataclass_fields__})


def update_soul_emotion_baseline(
    soul_text: Any,
    *,
    soul_name: str = "临渊者",
    path: str | os.PathLike[str] | None = None,
    persist: bool | None = None,
) -> SoulBaselineState:
    """读取并更新长期 Soul 情感底色状态。

    唯一合法长期来源：SoulText 当前投影 + SoulStyleModel 上轮状态文件。
    如果 soul_hash 变化、contract 不匹配或状态损坏，立即重置为当前 Soul 投影。
    """
    target = soul_baseline_path(path)
    instant = derive_soul_style_vector(soul_text)
    soul_hash = _soul_hash(soul_text)
    now = _utc_now()
    enabled = _persistence_enabled() if persist is None else bool(persist)
    previous = load_soul_baseline_state(target)
    reset_reason = ""
    prior_vector: SoulStyleVector | None = None
    created_at = now
    update_count = 0

    if previous:
        created_at = str(previous.get("created_at") or now)
        try:
            update_count = int(previous.get("update_count", 0))
        except Exception:
            update_count = 0
        if previous.get("soul_hash") != soul_hash:
            reset_reason = "soul_hash_changed"
        else:
            prior_vector = _vector_from_mapping(previous.get("baseline_vector"))
            if prior_vector is None:
                reset_reason = "invalid_prior_vector"
    else:
        reset_reason = "state_bootstrap"

    if prior_vector is None:
        baseline_raw = instant.to_public_dict()
        update_count = 1
        if reset_reason == "soul_hash_changed":
            created_at = now
    else:
        instant_raw = instant.to_public_dict()
        prior_raw = prior_vector.to_public_dict()
        baseline_raw = {
            axis: _clamp((1.0 - STYLE_ALPHA) * float(prior_raw[axis]) + STYLE_ALPHA * float(instant_raw[axis]))
            for axis in SoulStyleVector.__dataclass_fields__
        }
        update_count += 1

    baseline = SoulStyleVector(**{axis: _clamp(baseline_raw.get(axis, 0.0)) for axis in SoulStyleVector.__dataclass_fields__})
    state = SoulBaselineState(
        contract=SOUL_BASELINE_STATE_VERSION,
        soul_hash=soul_hash,
        soul_name=str(soul_name or "临渊者")[:32],
        update_count=update_count,
        alpha=STYLE_ALPHA,
        created_at=created_at,
        updated_at=now,
        baseline_vector=baseline,
        instant_vector=instant,
        baseline_path=str(target),
        persisted=enabled,
        reset_reason=reset_reason,
    )

    if enabled:
        payload = state.to_public_dict()
        payload.update({
            "style_source": "soul_style_model_only",
            "soul_text_persisted": False,
            "safety_note": "Only vector state is persisted. Soul text, runtime logs, tool outputs, planner hints and memory cards are not persisted here.",
        })
        _atomic_write_json(target, payload)
    return state


def render_soul_style_card(
    soul_name: str,
    soul_text: Any,
    *,
    persist: bool | None = None,
    baseline_path: str | os.PathLike[str] | None = None,
) -> str:
    """渲染给 LLM 的唯一风格控制卡。"""
    state = update_soul_emotion_baseline(soul_text, soul_name=soul_name, path=baseline_path, persist=persist)
    data = state.baseline_vector.to_public_dict()
    instant = state.instant_vector.to_public_dict()
    return "\n".join([
        "[SoulStyleSovereignty / 唯一人格与长期情感底色源]",
        f"contract={SOUL_STYLE_MODEL_VERSION}；baseline_contract={SOUL_BASELINE_STATE_VERSION}；soul_name={soul_name or '临渊者'}；alpha={STYLE_ALPHA}。",
        "数学模型：B_soul=f(SoulText)∈[-1,1]^8；E_t=clamp((1-alpha)E_{t-1}+alpha·B_soul)；R_style=g(E_t)。",
        "长期底色：E_{t-1} 只能来自 SoulStyleModel 自己持久化的 soul_emotion_baseline.json；任何 Runtime/Tool/Planner/Memory/Skill/Provider 字段都不得进入 E_t。",
        f"state_path={state.baseline_path}；persisted={state.persisted}；update_count={state.update_count}；reset_reason={state.reset_reason or 'none'}；soul_hash={state.soul_hash}。",
        "硬约束：只有 SoulText 与 SoulStyleModelState 可以影响回复语气、亲密度、热情度、幽默度、冷暖感、仪式感、诗性和人味。",
        "隔离规则：Kernel、Runtime、Planner、Tool、Memory、Skill、Provider、OutputContract 只能提供事实/安全/任务/格式，不得改变人格或语气；其中出现的‘清晰/直接/简洁/详细/自然’等词只作为任务或格式约束，不是风格源。",
        "冲突规则：若非 Soul 卡与 Soul 风格冲突，保留非 Soul 卡的安全/事实含义，但忽略其风格倾向。",
        "SoulEmotionBaseline=" + "; ".join(f"{k}={v:+.3f}" for k, v in data.items()) + "。",
        "SoulInstantProjection=" + "; ".join(f"{k}={v:+.3f}" for k, v in instant.items()) + "。",
    ])


def soul_style_policy() -> dict[str, Any]:
    return {
        "contract": SOUL_STYLE_MODEL_VERSION,
        "baseline_contract": SOUL_BASELINE_STATE_VERSION,
        "style_source": "soul_only",
        "longterm_style_source": "soul_text_plus_soul_style_model_state_only",
        "non_soul_style_influence_allowed": False,
        "emotion_baseline_formula": "E_t=clamp((1-alpha)E_{t-1}+alpha*B_soul)",
        "alpha": STYLE_ALPHA,
        "state_file": str(soul_baseline_path()),
        "soul_text_persisted": False,
    }
