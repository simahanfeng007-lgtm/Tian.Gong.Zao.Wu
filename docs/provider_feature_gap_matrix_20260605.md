# Provider Feature Gap Matrix

| provider_id | 内容 |
|---|---|
| `deepseek_v4` | `{"fallback_compatibility": "OpenAI-compatible branch can fall back to compatible text/tool-call providers when L5 permits", "unknown_or_unverified_fields": ["multimodal_input_supported", "file_input_supported", "image_input_supported", "audio_input_supported", "video_input_supported", "batch_supported", "safety_refusal_shape"]}` |
| `mimo` | `{"fallback_compatibility": "token_plan_api, ordinary_api, or open-weight local branch only through L3/L5/L4 envelopes", "unknown_or_unverified_fields": ["json_mode_supported", "thinking_mode_supported", "file_input_supported", "batch_supported", "ordinary_api_exact_endpoint", "safety_refusal_shape"]}` |
| `glm_5_1` | `{"fallback_compatibility": "OpenAI-compatible text/function-call provider fallback if L5 permits", "unknown_or_unverified_fields": ["json_mode_supported", "file_input_supported", "batch_supported", "rate_limit_policy_ref", "safety_refusal_shape"]}` |
| `minimax_m3` | `{"fallback_compatibility": "OpenAI/Anthropic-compatible coding/agentic fallback when L5 permits", "unknown_or_unverified_fields": ["structured_output_supported", "json_mode_supported", "file_input_supported", "audio_input_supported", "batch_supported", "safety_refusal_shape"]}` |
| `gpt_5_5` | `{"fallback_compatibility": "OpenAI Responses-compatible fallback via L3/L5/L4 envelopes", "unknown_or_unverified_fields": ["openai_chat_completions_compatibility", "audio_input_supported", "video_input_supported", "rate_limit_policy_ref_exact_numbers"]}` |
