from __future__ import annotations

# Single source of truth for Provider Settings write contract.
# Base URL is a normal configurable endpoint that may be shown as
# base_url_display; API Key remains write-only / digest-only.
PROVIDER_SETTINGS_WRITE_CONTRACT_VERSION = "tiangong.l6_73_5.provider_settings_write.v1"
SOUL_STYLE_MODEL_VERSION = "tiangong.l6_72_37.soul_longterm_style_sovereignty.v1"
SOUL_BASELINE_STATE_CONTRACT_VERSION = "tiangong.l6_72_37.soul_emotion_baseline_state.v1"

__all__ = (
    "PROVIDER_SETTINGS_WRITE_CONTRACT_VERSION",
    "SOUL_STYLE_MODEL_VERSION",
    "SOUL_BASELINE_STATE_CONTRACT_VERSION",
)
