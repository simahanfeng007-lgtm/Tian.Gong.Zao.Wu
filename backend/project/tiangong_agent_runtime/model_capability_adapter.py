"""L6.72.53 模型能力画像与被动执行策略建议层。

本模块只做“画像 / 记录 / 建议”，默认不改变 Planner 行为、不缩减工具、
不改前端展示、不触网、不读取凭证。它用于给后续 TaskStateLedger、
ContextWindowManager、AdaptiveWorkLoop 提供稳定元数据底座。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any


def _clean(value: Any, *, default: str = "") -> str:
    text = str(value or default).strip()
    return text[:180]


def _lower(value: Any) -> str:
    return _clean(value).lower()


@dataclass(frozen=True)
class ModelProfile:
    provider_id: str
    model_id: str
    protocol_family: str = "openai_compatible"
    context_window_estimate: int = 8192
    max_output_estimate: int = 4096
    supports_streaming: bool = True
    supports_json_mode: bool = False
    supports_tool_calling: bool = False
    supports_structured_output: bool = False
    supports_vision: bool = False
    supports_file_input: bool = False
    reasoning_strength: float = 0.50
    code_strength: float = 0.50
    planner_strength: float = 0.50
    json_reliability: float = 0.50
    instruction_following: float = 0.50
    long_context_reliability: float = 0.50
    tool_plan_reliability: float = 0.50
    refusal_sensitivity: float = 0.35
    latency_class: str = "unknown"
    cost_class: str = "unknown"
    observed_success_rate: float | None = None
    observed_plan_parse_rate: float | None = None
    observed_tool_success_rate: float | None = None
    observed_repair_success_rate: float | None = None
    recommended_role: str = "main_brain_guarded"
    confidence: float = 0.55
    source: str = "static_inference"
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def profile_id(self) -> str:
        raw = f"{self.provider_id}:{self.model_id}:{self.protocol_family}".encode("utf-8", errors="ignore")
        return "mp_" + sha256(raw).hexdigest()[:16]

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": "tiangong.l6_72_53.model_profile.v1",
            "profile_id": self.profile_id,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "protocol_family": self.protocol_family,
            "context_window_estimate": self.context_window_estimate,
            "max_output_estimate": self.max_output_estimate,
            "supports_streaming": self.supports_streaming,
            "supports_json_mode": self.supports_json_mode,
            "supports_tool_calling": self.supports_tool_calling,
            "supports_structured_output": self.supports_structured_output,
            "supports_vision": self.supports_vision,
            "supports_file_input": self.supports_file_input,
            "reasoning_strength": self.reasoning_strength,
            "code_strength": self.code_strength,
            "planner_strength": self.planner_strength,
            "json_reliability": self.json_reliability,
            "instruction_following": self.instruction_following,
            "long_context_reliability": self.long_context_reliability,
            "tool_plan_reliability": self.tool_plan_reliability,
            "refusal_sensitivity": self.refusal_sensitivity,
            "latency_class": self.latency_class,
            "cost_class": self.cost_class,
            "observed_success_rate": self.observed_success_rate,
            "observed_plan_parse_rate": self.observed_plan_parse_rate,
            "observed_tool_success_rate": self.observed_tool_success_rate,
            "observed_repair_success_rate": self.observed_repair_success_rate,
            "recommended_role": self.recommended_role,
            "confidence": self.confidence,
            "source": self.source,
            "notes": list(self.notes),
            "no_api_key": True,
            "passive_only": True,
        }


@dataclass(frozen=True)
class ModelExecutionPolicy:
    profile_id: str
    model_role: str
    max_plan_steps_per_round: int
    max_context_chars: int
    prompt_contract: str
    allowed_tool_families: tuple[str, ...]
    require_json_repair: bool
    require_quality_gate: bool
    allow_long_chain: bool
    fallback_model: str | None = None
    retry_strategy: str = "standard"
    micro_step_mode: bool = False
    passive_only: bool = True
    notes: tuple[str, ...] = field(default_factory=tuple)

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": "tiangong.l6_72_53.model_execution_policy.v1",
            "profile_id": self.profile_id,
            "model_role": self.model_role,
            "max_plan_steps_per_round": self.max_plan_steps_per_round,
            "max_context_chars": self.max_context_chars,
            "prompt_contract": self.prompt_contract,
            "allowed_tool_families": list(self.allowed_tool_families),
            "require_json_repair": self.require_json_repair,
            "require_quality_gate": self.require_quality_gate,
            "allow_long_chain": self.allow_long_chain,
            "fallback_model": self.fallback_model,
            "retry_strategy": self.retry_strategy,
            "micro_step_mode": self.micro_step_mode,
            "passive_only": self.passive_only,
            "notes": list(self.notes),
        }


class ModelCapabilityAdapter:
    """把 provider/model 配置解析为被动模型画像与策略建议。

    重要边界：本类不触网、不调用模型、不读 API Key；输出只作为元数据记录，
    默认不改变 Runtime 的真实执行行为。
    """

    def resolve_profile(self, model_config: Any | None) -> ModelProfile:
        provider = _lower(getattr(model_config, "provider", "") if model_config is not None else "") or "unknown"
        model = _lower(getattr(model_config, "model", "") if model_config is not None else "") or "unknown"
        protocol = "openai_compatible"
        notes: list[str] = ["passive_profile_only_no_execution_change"]

        if provider in {"disabled", "none"} or any(token in model for token in ("embedding", "bge", "rerank", "disabled")):
            return self._profile(
                provider,
                model,
                "disabled",
                context=1024,
                output=256,
                reasoning=0.05,
                code=0.05,
                planner=0.05,
                json_rel=0.20,
                follow=0.20,
                long_ctx=0.05,
                tool_plan=0.05,
                role="disabled",
                latency="unknown",
                cost="none",
                notes=tuple(notes + ["disabled_model_no_work"]),
            )
        if provider in {"weak", "subagent", "summary_only"} or any(token in model for token in ("weak", "tiny", "summary-only", "classifier", "toy")):
            return self._profile(
                provider,
                model,
                "subagent_only",
                context=4096,
                output=1024,
                reasoning=0.28,
                code=0.20,
                planner=0.24,
                json_rel=0.45,
                follow=0.45,
                long_ctx=0.20,
                tool_plan=0.20,
                role="subagent_only",
                latency="low",
                cost="low",
                notes=tuple(notes + ["subagent_only_no_main_brain_work"]),
            )
        if provider in {"anthropic", "claude", "fable"} or "claude" in model or "fable" in model:
            protocol = "anthropic_native"
            return self._profile(
                provider,
                model,
                protocol,
                context=200000 if "claude" in model or "fable" in model else 100000,
                output=8192,
                reasoning=0.88,
                code=0.84,
                planner=0.88,
                json_rel=0.78,
                follow=0.88,
                long_ctx=0.82,
                tool_plan=0.82,
                role="main_brain_full",
                latency="medium",
                cost="high",
                notes=tuple(notes + ["strong_reasoning_profile"]),
            )
        if provider == "openai" or model.startswith("gpt") or "o3" in model or "o4" in model:
            protocol = "openai_native"
            return self._profile(
                provider,
                model,
                protocol,
                context=128000,
                output=8192,
                reasoning=0.86,
                code=0.86,
                planner=0.86,
                json_rel=0.86,
                follow=0.86,
                long_ctx=0.80,
                tool_plan=0.85,
                role="main_brain_full",
                latency="medium",
                cost="medium_high",
                notes=tuple(notes + ["strong_structured_output_profile"]),
            )
        if provider == "deepseek" or "deepseek" in model:
            return self._profile(
                provider,
                model,
                protocol,
                context=64000 if "v4" in model or "r1" in model else 32768,
                output=8192,
                reasoning=0.76,
                code=0.82,
                planner=0.76,
                json_rel=0.68,
                follow=0.74,
                long_ctx=0.66,
                tool_plan=0.70,
                role="main_brain_guarded",
                latency="medium",
                cost="medium",
                notes=tuple(notes + ["json_repair_recommended"]),
            )
        if provider in {"qwen", "dashscope"} or "qwen" in model:
            return self._profile(
                provider,
                model,
                protocol,
                context=32768,
                output=4096,
                reasoning=0.68,
                code=0.74,
                planner=0.66,
                json_rel=0.64,
                follow=0.66,
                long_ctx=0.58,
                tool_plan=0.62,
                role="micro_planner",
                latency="medium",
                cost="medium_low",
                notes=tuple(notes + ["micro_step_mode_recommended"]),
            )
        if provider in {"gemini", "google"} or "gemini" in model:
            protocol = "gemini_native"
            return self._profile(
                provider,
                model,
                protocol,
                context=1000000 if "1.5" in model or "2" in model else 128000,
                output=8192,
                reasoning=0.74,
                code=0.70,
                planner=0.70,
                json_rel=0.66,
                follow=0.72,
                long_ctx=0.84,
                tool_plan=0.66,
                role="main_brain_guarded",
                latency="medium",
                cost="medium",
                notes=tuple(notes + ["long_context_strong_json_guarded"]),
            )
        if provider in {"glm", "zhipu"} or "glm" in model:
            return self._profile(
                provider,
                model,
                protocol,
                context=32768,
                output=4096,
                reasoning=0.62,
                code=0.58,
                planner=0.58,
                json_rel=0.58,
                follow=0.62,
                long_ctx=0.52,
                tool_plan=0.56,
                role="micro_planner",
                latency="medium",
                cost="medium_low",
                notes=tuple(notes + ["guarded_micro_planner_profile"]),
            )
        if provider in {"minimax", "mimo"} or "minimax" in model or "mimo" in model:
            return self._profile(
                provider,
                model,
                protocol,
                context=32768,
                output=4096,
                reasoning=0.56,
                code=0.52,
                planner=0.52,
                json_rel=0.54,
                follow=0.58,
                long_ctx=0.50,
                tool_plan=0.50,
                role="micro_planner",
                latency="medium",
                cost="medium_low",
                notes=tuple(notes + ["short_schema_recommended"]),
            )
        if provider in {"mock", "offline", "test"} or "mock" in model or "sample" in model:
            return self._profile(
                provider,
                model,
                "offline_mock",
                context=8192,
                output=2048,
                reasoning=0.40,
                code=0.40,
                planner=0.45,
                json_rel=0.95,
                follow=0.70,
                long_ctx=0.35,
                tool_plan=0.55,
                role="micro_planner",
                latency="low",
                cost="none",
                notes=tuple(notes + ["offline_test_profile"]),
            )
        return self._profile(
            provider,
            model,
            protocol,
            context=8192,
            output=2048,
            reasoning=0.50,
            code=0.50,
            planner=0.50,
            json_rel=0.50,
            follow=0.50,
            long_ctx=0.45,
            tool_plan=0.50,
            role="main_brain_guarded",
            latency="unknown",
            cost="unknown",
            notes=tuple(notes + ["unknown_model_safe_default"]),
        )

    def resolve_policy(self, profile: ModelProfile, activation_form: Any | None = None) -> ModelExecutionPolicy:
        role = profile.recommended_role
        notes = ["passive_policy_record_compatible", "active_enforcement_available_via_ModelExecutionPolicyEngine_L6_72_58"]
        if role == "main_brain_full":
            return ModelExecutionPolicy(
                profile_id=profile.profile_id,
                model_role=role,
                max_plan_steps_per_round=12,
                max_context_chars=min(profile.context_window_estimate // 2, 64000),
                prompt_contract="strict_json",
                allowed_tool_families=("file", "document", "code", "terminal", "web", "delivery", "analysis"),
                require_json_repair=profile.json_reliability < 0.82,
                require_quality_gate=True,
                allow_long_chain=True,
                retry_strategy="standard_then_repair",
                micro_step_mode=False,
                notes=tuple(notes),
            )
        if role == "main_brain_guarded":
            return ModelExecutionPolicy(
                profile_id=profile.profile_id,
                model_role=role,
                max_plan_steps_per_round=5,
                max_context_chars=min(profile.context_window_estimate // 3, 24000),
                prompt_contract="short_json",
                allowed_tool_families=("file", "document", "code", "terminal", "delivery", "analysis"),
                require_json_repair=True,
                require_quality_gate=True,
                allow_long_chain=True,
                retry_strategy="short_json_then_micro_step",
                micro_step_mode=True,
                notes=tuple(notes + ["guarded_models_should_use_short_plans"]),
            )
        if role == "micro_planner":
            return ModelExecutionPolicy(
                profile_id=profile.profile_id,
                model_role=role,
                max_plan_steps_per_round=3,
                max_context_chars=min(profile.context_window_estimate // 4, 12000),
                prompt_contract="choice_or_short_json",
                allowed_tool_families=("file", "document", "analysis", "quality"),
                require_json_repair=True,
                require_quality_gate=True,
                allow_long_chain=False,
                retry_strategy="single_step_then_rule_fallback",
                micro_step_mode=True,
                notes=tuple(notes + ["not_enforced_in_l67253"]),
            )
        return ModelExecutionPolicy(
            profile_id=profile.profile_id,
            model_role=role,
            max_plan_steps_per_round=1,
            max_context_chars=4000,
            prompt_contract="single_choice",
            allowed_tool_families=("analysis",),
            require_json_repair=True,
            require_quality_gate=True,
            allow_long_chain=False,
            retry_strategy="subagent_only",
            micro_step_mode=True,
            notes=tuple(notes + ["weak_model_should_not_be_main_brain"]),
        )

    def _profile(
        self,
        provider: str,
        model: str,
        protocol: str,
        *,
        context: int,
        output: int,
        reasoning: float,
        code: float,
        planner: float,
        json_rel: float,
        follow: float,
        long_ctx: float,
        tool_plan: float,
        role: str,
        latency: str,
        cost: str,
        notes: tuple[str, ...],
    ) -> ModelProfile:
        return ModelProfile(
            provider_id=provider or "unknown",
            model_id=model or "unknown",
            protocol_family=protocol,
            context_window_estimate=int(context),
            max_output_estimate=int(output),
            supports_streaming=True,
            supports_json_mode=json_rel >= 0.75,
            supports_tool_calling=False,
            supports_structured_output=json_rel >= 0.70,
            reasoning_strength=float(reasoning),
            code_strength=float(code),
            planner_strength=float(planner),
            json_reliability=float(json_rel),
            instruction_following=float(follow),
            long_context_reliability=float(long_ctx),
            tool_plan_reliability=float(tool_plan),
            recommended_role=role,
            latency_class=latency,
            cost_class=cost,
            confidence=0.72 if role in {"main_brain_full", "main_brain_guarded"} else 0.62,
            notes=notes,
        )
