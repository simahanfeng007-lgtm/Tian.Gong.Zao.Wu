# Provider Endpoint Matrix

| provider_id | 内容 |
|---|---|
| `deepseek_v4` | `{"auth_scheme_ref": "credential-handle:bearer", "base_url_ref": "official-ref:deepseek-base-url-openai-and-anthropic", "protocol_family": ["openai_chat_completions", "anthropic_messages"], "request_api_style": "OpenAI Chat Completions compatible / Anthropic compatible"}` |
| `mimo` | `{"auth_scheme_ref": "credential-handle:token_plan_api_or_ordinary_api", "base_url_ref": "official-ref:mimo-api-platform; supports token_plan_api and ordinary_api via credential scoped endpoint ref, never hardcoded", "protocol_family": ["provider_native", "openai_chat_completions:api-platform-compatible", "local_service_port"], "request_api_style": "MiMo API Platform; supports token_plan_api and ordinary_api; open-weight local service port reservation"}` |
| `glm_5_1` | `{"auth_scheme_ref": "credential-handle:bearer", "base_url_ref": "official-ref:zai-general-and-coding-paas-v4-endpoints", "protocol_family": ["openai_chat_completions", "provider_native"], "request_api_style": "OpenAI-compatible chat.completions with Z.AI parameters"}` |
| `minimax_m3` | `{"auth_scheme_ref": "credential-handle:bearer", "base_url_ref": "official-ref:minimax-openai-v1-and-anthropic-base-url", "protocol_family": ["openai_chat_completions", "anthropic_messages", "provider_native"], "request_api_style": "OpenAI-compatible or Anthropic-compatible chat/messages"}` |
| `gpt_5_5` | `{"auth_scheme_ref": "credential-handle:bearer", "base_url_ref": "official-ref:openai-responses-api-base-url", "protocol_family": ["openai_responses", "openai_chat_completions:compatibility_unknown"], "request_api_style": "OpenAI Responses API"}` |
