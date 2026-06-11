from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

from tiangong_agent_shell.prompt_compiler import build_desktop_context, compile_prompt
from tiangong_agent_shell.soul_style_model import (
    SOUL_BASELINE_STATE_VERSION,
    SOUL_STYLE_MODEL_VERSION,
    derive_soul_style_vector,
    load_soul_baseline_state,
    soul_style_policy,
    update_soul_emotion_baseline,
)


@contextmanager
def env_patch(**values: str):
    old = {k: os.environ.get(k) for k in values}
    try:
        for k, v in values.items():
            os.environ[k] = v
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "soul_emotion_baseline.json"
        warm = "温柔、自然、不机械、有陪伴感，但稳定、可信、会复检。"
        sharp = "冷静、锋利、直接、果断、执行力强，少废话。"

        first = update_soul_emotion_baseline(warm, soul_name="临渊者", path=state_path)
        require(first.contract == SOUL_BASELINE_STATE_VERSION, "baseline state contract mismatch")
        require(first.update_count == 1, "first update should bootstrap state")
        require(first.reset_reason == "state_bootstrap", "first update reset reason should be bootstrap")
        require(state_path.exists(), "baseline state file should be persisted")
        data = json.loads(state_path.read_text(encoding="utf-8"))
        require("Soul 原文" not in json.dumps(data, ensure_ascii=False), "state must not persist soul text")
        require(data.get("style_source") == "soul_style_model_only", "state source must be self-owned")

        second = update_soul_emotion_baseline(warm, soul_name="临渊者", path=state_path)
        require(second.update_count == 2, "same soul should update EMA count")
        require(second.soul_hash == first.soul_hash, "same soul should keep hash")
        require(second.baseline_vector.warmth >= first.baseline_vector.warmth - 0.01, "warmth should remain stable under same soul")

        third = update_soul_emotion_baseline(sharp, soul_name="临渊者", path=state_path)
        require(third.update_count == 1, "changed soul should reset baseline count")
        require(third.reset_reason == "soul_hash_changed", "changed soul must reset stale baseline")
        require(third.baseline_vector.directness > first.baseline_vector.directness, "sharp soul should produce higher directness after reset")

        loaded = load_soul_baseline_state(state_path)
        require(bool(loaded), "persisted state should be loadable")
        require(loaded["contract"] == SOUL_BASELINE_STATE_VERSION, "loaded state contract mismatch")

        no_write_path = Path(tmp) / "readonly_state.json"
        disabled = update_soul_emotion_baseline(warm, soul_name="临渊者", path=no_write_path, persist=False)
        require(disabled.persisted is False, "persist=False should be reflected")
        require(not no_write_path.exists(), "persist=False must not write file")

        with env_patch(
            TIANGONG_SOUL_NAME="临渊者",
            TIANGONG_SOUL_PROMPT=warm,
            TIANGONG_SOUL_BASELINE_PATH=str(state_path),
            TIANGONG_RESPONSE_STYLE="外部强制：机械播报腔",
            TIANGONG_LANGUAGE_POLICY="外部强制：油腻营销腔",
        ):
            prompt = compile_prompt(build_desktop_context()).system_prompt
        require("SoulStyleSovereignty" in prompt, "prompt must include SoulStyle card")
        require(SOUL_STYLE_MODEL_VERSION in prompt, "prompt must include L6.72.37 style contract")
        require("SoulEmotionBaseline" in prompt, "prompt must expose long-term baseline vector")
        require("SoulInstantProjection" in prompt, "prompt must expose instant soul projection")
        require("外部强制" not in prompt, "external style env must not leak into prompt")
        require("SoulStyleModelState" in prompt, "prompt must declare persistent state as only long-term source")

        policy = soul_style_policy()
        require(policy["style_source"] == "soul_only", "policy style_source must be soul_only")
        require(policy["longterm_style_source"] == "soul_text_plus_soul_style_model_state_only", "longterm source must be isolated")
        require(policy["non_soul_style_influence_allowed"] is False, "non-soul style influence must be blocked")

        warm_vec = derive_soul_style_vector(warm)
        sharp_vec = derive_soul_style_vector(sharp)
        require(warm_vec.warmth > sharp_vec.warmth, "warm soul should remain warmer than sharp soul")

    print("PASS L6.72.37 Soul long-term baseline persistence smoke")


if __name__ == "__main__":
    main()
