# L0 第 1 阶段开发日志：基础地基

- 日期：2026-06-03
- 范围：identity.py、time.py、result.py、errors.py、serialization.py、trace.py
- 层级：L0 零依赖原语层

## 目标

建立 L0 基础事实语言：稳定身份、时间值、Result-first 结果、错误事实、稳定序列化与追踪上下文。

## 已完成模块与对象

- `identity.py`：`CoreId`、`RefId`、`TypedRef`、`IdPrefix`、`new_core_id()`、`validate_core_id()`。
- `time.py`：`Timestamp`、`Duration`、`Deadline`、`TimeRange`、`TemporalWindow`、`SequenceNo`、`LogicalTime`、`LogicalClock`、`ClockSourceRef`、`ClockKind`。
- `result.py`：`CoreResult`、`ResultStatus`、`ok()`、`err()`。
- `errors.py`：`CoreError`、`ErrorCode`、`ErrorSeverity`。
- `serialization.py`：`to_primitive()`、`stable_json_dumps()`、`stable_hash()`、`from_primitive()`。
- `trace.py`：`TraceId`、`SpanId`、`CorrelationId`、`CausationId`、`ActorId`、`ScopeId`、`TraceContext`、`CausalEventMetadata`。

## 设计取舍

- 使用 `@dataclass(frozen=True, slots=True)` 保持不可变和值对象语义。
- `validate_core_id()` 采用 Result-first；构造器中的 `ValueError` 只用于不可恢复的程序员错误输入。
- `TraceContext` 保存 trace/span/correlation 等传播上下文；`causation_id` 归属 `CausalEventMetadata`，避免同一因果字段在两个对象中重复。

## 本轮修复记录

- 为阶段 1 模块补中文边界说明。
- 为缺失兜底的枚举补 `UNKNOWN = "unknown"`：`IdPrefix`、`ClockKind`、`ResultStatus`、`ErrorSeverity`。
- 新增阶段 1 聚合测试 `tests/test_l0_phase1_contract.py`。

## 测试命令与结果

- `python -m pytest tests/test_l0_phase1* -q`：4 passed。
- `python -m pytest tests/test_l0_serialization.py -q`：4 passed。
- `python -m pytest tests/test_l0_stable_hash.py -q`：3 passed。

## 未做事项

- 未引入任何第三方依赖。
- 未实现系统时钟读取、调度器、事件上报、文件读写或网络访问。
