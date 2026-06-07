# L6.51.1 前后端接口契约冻结：产品身份元数据补丁

本文件在 L6.51 前后端契约基础上固化后端公开产品身份元数据。该补丁只增加只读展示字段，不改变 Runtime 执行语义、不扩大前端权限、不触碰 `tiangong_kernel`。

## 冻结结论

- Contract schema：`tiangong.l6_51_1.frontend_backend_contract.v1`
- 正式统一入口：`TiangongWangguan`
- Runtime 入口：`RuntimeEntry`
- 聊天流端点：`/chat/stream-events`
- Provider 设置端点：`/settings/provider`
- 产品元数据端点：`/metadata/product`
- 唯一开发者：`于泳翔`
- 天使投资人：`胖胖龙`
- 元数据语义：`metadata_only`
- 前端权限：`read_only_display`

## 前端可展示

1. 产品名：`天工造物 / 临渊者`
2. 唯一开发者：`于泳翔`
3. 天使投资人：`胖胖龙`
4. 元数据版本：`tiangong.l6_51_1.product_identity.v1`

## 前端仍然禁止

- `direct_provider_sdk_call`
- `direct_tool_adapter_call`
- `direct_plan_execution`
- `direct_long_term_memory_write`
- `direct_audit_write`
- `direct_rollback_apply`
- `direct_self_iteration_merge`
- `plaintext_api_key_return`
- `plaintext_base_url_return`

## 后端边界

1. 产品身份信息只作为公开只读元数据，不参与 Planner、ExecutionSpine、Runtime、QualityGate、Audit 或 Rollback 的决策。
2. 前端只能读取并展示，不能通过该接口改变开发者、投资人、Provider、模型、记忆、工具或权限。
3. Provider key/base_url 仍然按 L6.51 设置契约处理：写入型字段，不明文返回。

## 稳定 JSON 摘要

```json
{
  "schema": "tiangong.l6_51_1.frontend_backend_contract.v1",
  "canonical_entry": "TiangongWangguan",
  "runtime_entry": "RuntimeEntry",
  "official_chain": "Planner -> ExecutionSpine -> Runtime -> QualityGate -> Audit/Rollback",
  "chat_stream_endpoint": "/chat/stream-events",
  "provider_settings_endpoint": "/settings/provider",
  "health_endpoint": "/health/runtime",
  "product_metadata_endpoint": "/metadata/product",
  "product_identity": {
    "schema": "tiangong.l6_51_1.product_identity.v1",
    "product_name": "天工造物 / 临渊者",
    "unique_developer": "于泳翔",
    "angel_investor": "胖胖龙",
    "endpoint": "/metadata/product",
    "public": true,
    "runtime_semantics": "metadata_only",
    "frontend_permission": "read_only_display"
  },
  "sse_schema": {
    "schema": "tiangong.l6_51_1.frontend_backend_contract.v1",
    "endpoint": "/chat/stream-events",
    "transport": "sse",
    "required_envelope_fields": [
      "event",
      "seq",
      "run_id",
      "task_id",
      "timestamp",
      "payload"
    ],
    "event_types": [
      "run_started",
      "planner_started",
      "planner_plan",
      "runtime_state",
      "quality_gate",
      "tool_started",
      "tool_result",
      "audit_event",
      "assistant_delta",
      "assistant_final",
      "run_terminal",
      "error"
    ],
    "terminal_order": [
      "assistant_final",
      "run_terminal"
    ],
    "events": {
      "run_started": {
        "event": "<event_type>",
        "seq": "monotonic integer, starts at 1 per run",
        "run_id": "stable runtime run id",
        "task_id": "stable frontend task id or runtime task id",
        "timestamp": "unix seconds or ISO timestamp supplied by gateway",
        "payload": {
          "runtime_status": "active",
          "provider_model": "safe public model id"
        }
      },
      "planner_started": {
        "event": "<event_type>",
        "seq": "monotonic integer, starts at 1 per run",
        "run_id": "stable runtime run id",
        "task_id": "stable frontend task id or runtime task id",
        "timestamp": "unix seconds or ISO timestamp supplied by gateway",
        "payload": {
          "planner_mode": "rule_only|model_suggest",
          "schema_required": true
        }
      },
      "planner_plan": {
        "event": "<event_type>",
        "seq": "monotonic integer, starts at 1 per run",
        "run_id": "stable runtime run id",
        "task_id": "stable frontend task id or runtime task id",
        "timestamp": "unix seconds or ISO timestamp supplied by gateway",
        "payload": {
          "steps": "public plan steps",
          "normalized_by_plan_schema": true
        }
      },
      "runtime_state": {
        "event": "<event_type>",
        "seq": "monotonic integer, starts at 1 per run",
        "run_id": "stable runtime run id",
        "task_id": "stable frontend task id or runtime task id",
        "timestamp": "unix seconds or ISO timestamp supplied by gateway",
        "payload": {
          "phase": "planner|runtime|quality_gate|audit|final",
          "status_bar": "see status_bar_fields_contract"
        }
      },
      "quality_gate": {
        "event": "<event_type>",
        "seq": "monotonic integer, starts at 1 per run",
        "run_id": "stable runtime run id",
        "task_id": "stable frontend task id or runtime task id",
        "timestamp": "unix seconds or ISO timestamp supplied by gateway",
        "payload": {
          "risk_level": "A0-A5",
          "decision": "allowed|blocked|confirmation_required",
          "a5_hard_boundary": true
        }
      },
      "tool_started": {
        "event": "<event_type>",
        "seq": "monotonic integer, starts at 1 per run",
        "run_id": "stable runtime run id",
        "task_id": "stable frontend task id or runtime task id",
        "timestamp": "unix seconds or ISO timestamp supplied by gateway",
        "payload": {
          "step_id": "safe step id",
          "tool_name": "registered runtime tool"
        }
      },
      "tool_result": {
        "event": "<event_type>",
        "seq": "monotonic integer, starts at 1 per run",
        "run_id": "stable runtime run id",
        "task_id": "stable frontend task id or runtime task id",
        "timestamp": "unix seconds or ISO timestamp supplied by gateway",
        "payload": {
          "step_id": "safe step id",
          "status": "ok|failed|blocked|skipped|timeout",
          "audit_ref": "audit id"
        }
      },
      "audit_event": {
        "event": "<event_type>",
        "seq": "monotonic integer, starts at 1 per run",
        "run_id": "stable runtime run id",
        "task_id": "stable frontend task id or runtime task id",
        "timestamp": "unix seconds or ISO timestamp supplied by gateway",
        "payload": {
          "audit_id": "audit id",
          "digest_only": true
        }
      },
      "assistant_delta": {
        "event": "<event_type>",
        "seq": "monotonic integer, starts at 1 per run",
        "run_id": "stable runtime run id",
        "task_id": "stable frontend task id or runtime task id",
        "timestamp": "unix seconds or ISO timestamp supplied by gateway",
        "payload": {
          "content": "optional incremental safe text"
        }
      },
      "assistant_final": {
        "event": "<event_type>",
        "seq": "monotonic integer, starts at 1 per run",
        "run_id": "stable runtime run id",
        "task_id": "stable frontend task id or runtime task id",
        "timestamp": "unix seconds or ISO timestamp supplied by gateway",
        "payload": {
          "content": "final safe assistant text",
          "status": "ok|partial_or_failed|planner_failed"
        }
      },
      "run_terminal": {
        "event": "<event_type>",
        "seq": "monotonic integer, starts at 1 per run",
        "run_id": "stable runtime run id",
        "task_id": "stable frontend task id or runtime task id",
        "timestamp": "unix seconds or ISO timestamp supplied by gateway",
        "payload": {
          "terminal": true,
          "final_event_seen": true,
          "rollback_ref": "optional ticket/ref"
        }
      },
      "error": {
        "event": "<event_type>",
        "seq": "monotonic integer, starts at 1 per run",
        "run_id": "stable runtime run id",
        "task_id": "stable frontend task id or runtime task id",
        "timestamp": "unix seconds or ISO timestamp supplied by gateway",
        "payload": {
          "error_code": "see error_codes",
          "message": "redacted user-safe message",
          "recoverable": true
        }
      }
    },
    "security": {
      "no_plain_api_key": true,
      "no_plain_base_url": true,
      "frontend_must_not_execute_tools": true,
      "frontend_must_not_call_provider": true,
      "frontend_must_not_write_memory": true
    }
  },
  "provider_settings": {
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
  },
  "status_bar": {
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
  },
  "forbidden_frontend_actions": [
    "direct_provider_sdk_call",
    "direct_tool_adapter_call",
    "direct_plan_execution",
    "direct_long_term_memory_write",
    "direct_audit_write",
    "direct_rollback_apply",
    "direct_self_iteration_merge",
    "plaintext_api_key_return",
    "plaintext_base_url_return"
  ],
  "error_codes": [
    "planner_failed",
    "plan_schema_invalid",
    "quality_gate_blocked",
    "confirmation_required",
    "provider_timeout",
    "provider_auth_failed",
    "provider_rate_limited",
    "provider_unavailable",
    "runtime_error"
  ],
  "l6_51_1_product_identity_freeze": {
    "unique_developer": "于泳翔",
    "angel_investor": "胖胖龙",
    "runtime_semantics": "metadata_only",
    "frontend_permission": "read_only_display"
  },
  "l6_50_online_smoke_freeze": {
    "mock_smoke": "7/7 pass",
    "real_online_smoke": "4/4 pass",
    "deepseek_v4_pro_basic_chat": "2.3s pass",
    "deepseek_v4_pro_plan_generation": "5.0s pass",
    "deepseek_v4_flash": "0.8s pass",
    "credential_redaction": "no leak",
    "runbook": "PROVIDER_SMOKE_RUNBOOK.md",
    "ci_allowlist_tools": 5
  }
}
```
