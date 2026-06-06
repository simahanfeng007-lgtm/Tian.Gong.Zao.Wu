# L6.51.1 底部状态栏字段契约

L6.51.1 未改变底部状态栏字段集合。产品身份信息不进入运行状态栏主链，只可在关于页/设置页只读展示。

```json
{
  "schema": "tiangong.l6_51_1.frontend_backend_contract.v1",
  "fields": {
    "runtime_status": "idle|active|planner_failed|partial_or_failed|ok|error",
    "provider_model": "safe provider/model label, no endpoint/key",
    "budget_pool": "main|auxiliary|diagnostic|child_agent|long_chain|extreme|unknown",
    "budget_used_ratio": "0.0-1.0 or not_reported",
    "gate_status": "A0-A4 allowed/confirmation or A5 blocked",
    "audit_id": "latest audit id or digest ref",
    "memory_mode": "readonly|writable_by_runtime|disabled; frontend never writes directly",
    "tools_allowed": "integer count of runtime-registered allowed tools",
    "latency_ms": "integer latency from gateway/runtime measurement"
  },
  "required_fields": [
    "runtime_status",
    "provider_model",
    "budget_pool",
    "budget_used_ratio",
    "gate_status",
    "audit_id",
    "memory_mode",
    "tools_allowed",
    "latency_ms"
  ],
  "minimal_home_rule": {
    "fixed_chat_input_required": true,
    "home_should_stay_minimal": true,
    "no_monitor_wall_by_default": true
  }
}
```
