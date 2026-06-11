# L6.51.1 Provider 设置契约

L6.51.1 未改变 Provider 设置安全边界。`api_key/base_url` 仍为写入型字段，不明文返回。

```json
{
  "schema": "tiangong.l6_51_1.frontend_backend_contract.v1",
  "endpoint": "/settings/provider",
  "read_fields": [
    "provider",
    "model",
    "base_url_digest",
    "api_key_configured",
    "timeout",
    "stream",
    "planner_mode",
    "tool_execution_mode"
  ],
  "write_only_fields": [
    "api_key",
    "base_url"
  ],
  "forbidden_response_fields": [
    "api_key",
    "authorization",
    "bearer",
    "token",
    "secret",
    "base_url",
    "endpoint"
  ],
  "storage_boundary": "gateway_or_controlled_config_layer_only",
  "frontend_storage": {
    "local_storage_plaintext": false,
    "logs_plaintext": false
  },
  "deepseek_alias_env": [
    "ENV_REDACTED",
    "URL_ENV_REDACTED",
    "MODEL_ENV_REDACTED"
  ],
  "canonical_env": [
    "TIANGONG_API_KEY",
    "TIANGONG_BASE_URL",
    "TIANGONG_MODEL"
  ],
  "model_routing_hint": {
    "deepseek-v4-flash": "fast_readonly_or_small_tasks",
    "deepseek-v4-pro": "planner_or_complex_tasks"
  }
}
```
