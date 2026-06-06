# Provider Error Taxonomy Matrix

| provider_id | 内容 |
|---|---|
| `deepseek_v4` | `{"error_code_shape": "HTTP status + provider error message", "retry_policy_hint": "retry transient 5xx/503/429 with L5 budget; never retry auth/balance/invalid params", "standard_failure_envelope": "ModelProviderFailureEnvelope:deepseek_v4"}` |
| `mimo` | `{"error_code_shape": "HTTP status table 400/401/402/403/404/421/429/500/503 with MiMo platform error guidance", "retry_policy_hint": "unknown; only L5-governed transient retry allowed after factsheet refresh", "standard_failure_envelope": "ModelProviderFailureEnvelope:mimo"}` |
| `glm_5_1` | `{"error_code_shape": "HTTP status + Z.AI error code/message", "retry_policy_hint": "retry transient 5xx/429 only under L5 budget; do not retry auth/invalid params", "standard_failure_envelope": "ModelProviderFailureEnvelope:glm_5_1"}` |
| `minimax_m3` | `{"error_code_shape": "HTTP status + MiniMax error body/code", "retry_policy_hint": "retry transient 5xx/429 under L5 budget; do not retry invalid/auth errors", "standard_failure_envelope": "ModelProviderFailureEnvelope:minimax_m3"}` |
| `gpt_5_5` | `{"error_code_shape": "HTTP status + OpenAI error object", "retry_policy_hint": "retry transient 5xx/429 after L5 budget/rate permit; do not retry auth/invalid request", "standard_failure_envelope": "ModelProviderFailureEnvelope:gpt_5_5"}` |
