# L6.51.1 Runtime SSE 事件契约

Schema：`tiangong.l6_51_1.frontend_backend_contract.v1`

本文件沿用 L6.51 SSE 事件顺序，L6.51.1 只增加产品身份元数据契约，不改变 SSE 执行事件语义。

```json
{
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
}
```
