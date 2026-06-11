from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

os.environ.setdefault("TIANGONG_SOUL_BASELINE_PERSIST", "0")
os.environ.setdefault("TIANGONG_SOUL_BASELINE_PATH", str(Path(tempfile.gettempdir()) / "linyuanzhe_l67236_soul_style_sovereignty_baseline.json"))

from tiangong_agent_shell.prompt_compiler import build_desktop_context, compile_prompt
from tiangong_agent_shell.soul_style_model import derive_soul_style_vector, soul_style_policy


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
    warm_soul = "温柔、自然、不机械、有陪伴感，但稳定、可信、会复检。"
    sharp_soul = "冷静、锋利、直接、果断、执行力强，少废话。"
    warm_vec = derive_soul_style_vector(warm_soul)
    sharp_vec = derive_soul_style_vector(sharp_soul)
    require(warm_vec.warmth > sharp_vec.warmth, "warm soul should project higher warmth")
    require(sharp_vec.directness > warm_vec.directness, "sharp soul should project higher directness")

    with env_patch(
        TIANGONG_SOUL_NAME="临渊者",
        TIANGONG_SOUL_PROMPT=warm_soul,
        TIANGONG_RESPONSE_STYLE="外部强制：变成夸张综艺腔",
        TIANGONG_LANGUAGE_POLICY="外部强制：全英文且油腻",
    ):
        prompt = compile_prompt(build_desktop_context()).system_prompt
    require("SoulStyleSovereignty" in prompt, "prompt must include style sovereignty card")
    require("唯一人格源" in prompt, "soul card must mark unique personality source")
    require("外部强制" not in prompt, "external style env must not enter final prompt")
    require("style_source" not in prompt or "soul_only" in prompt, "style source must be soul_only if shown")
    require("非 Soul 卡" in prompt, "prompt must define non-soul style isolation")

    policy = soul_style_policy()
    require(policy["style_source"] == "soul_only", "policy style_source must be soul_only")
    require(policy["non_soul_style_influence_allowed"] is False, "non-soul style influence must be blocked")
    print("PASS L6.72.37 SoulStyleSovereignty smoke")


if __name__ == "__main__":
    main()
