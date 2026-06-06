# 天工造物 L1 第一阶段开发日志

生成日期：2026-06-03
阶段名称：L1 第一阶段——协议骨架与边界说明

## 本阶段目标

本阶段在 L0 零依赖原语层之上建立 L1 端口协议层的最小公共地基，只定义协议、身份、边界说明、结果、错误、健康、生命周期与信封对象。

本阶段服务两个上位方向：

1. 工程生命体：为后续状态层、运行编排层、外部适配层、插件宿主层、子系统插件层提供稳定端口语言。
2. 大模型执行力与绝对边界：边界只表达能做什么、不能做什么、越界原因和替代路径，不把协议层写成审批链或执行器。

## 新增源码清单

新增目录：

- `tiangong_kernel/l1_ports/`

新增源码文件：

- `tiangong_kernel/l1_ports/__init__.py`
- `tiangong_kernel/l1_ports/base.py`
- `tiangong_kernel/l1_ports/port_result.py`
- `tiangong_kernel/l1_ports/port_error.py`
- `tiangong_kernel/l1_ports/port_boundary.py`
- `tiangong_kernel/l1_ports/port_health.py`
- `tiangong_kernel/l1_ports/port_lifecycle.py`
- `tiangong_kernel/l1_ports/envelope.py`

## 新增测试清单

- `tests/test_l1_no_l2_imports.py`
- `tests/test_l1_no_third_party_imports.py`
- `tests/test_l1_no_real_io.py`
- `tests/test_l1_ports_are_abstract.py`
- `tests/test_l1_ports_return_core_result.py`
- `tests/test_l1_uses_l0_primitives.py`
- `tests/test_l1_no_execution_keywords.py`
- `tests/test_l1_chinese_docstrings.py`

## 每个端口对象职责

### `base.py`

定义 L1 端口基础协议与身份对象：

- `PortName`：端口名称值对象。
- `PortKind`：端口类别枚举。
- `PortPlane`：控制面、执行面、观察面三面结构枚举。
- `PortDirection`：端口方向枚举。
- `PortVisibility`：系统内部可见性枚举，不代表大模型可见。
- `PortIdentity`：端口身份声明。
- `BasePort`：抽象端口协议，只要求端口声明身份、边界、健康和生命周期。

### `port_result.py`

定义端口结果表达：

- `PortResultStatus`：端口结果状态。
- `PortSuccessMetadata`：成功元数据。
- `PortFailure`：失败说明。
- `PortResult`：包裹 L0 `CoreResult` 的端口结果对象。

### `port_error.py`

定义端口错误边界：

- `PortErrorKind`：错误类别。
- `PortErrorPolicy`：错误返回策略声明。
- `PortFailureHint`：失败提示。
- `PortErrorBoundary`：端口错误边界说明。

### `port_boundary.py`

定义端口边界说明：

- `BoundarySeverity`：边界严重度。
- `BoundaryHint`：越界原因、修正建议、替代路径。
- `BoundaryRule`：边界规则声明。
- `BoundaryViolation`：越界事实。
- `PortBoundary`：端口边界说明汇总。

### `port_health.py`

定义端口健康声明：

- `PortHealthStatus`：健康状态。
- `PortHealthSignal`：健康信号。
- `PortHealthBoundary`：健康声明边界。
- `PortHealthDeclaration`：健康声明汇总。

### `port_lifecycle.py`

定义端口生命周期声明：

- `PortLifecycleState`：生命周期状态。
- `PortLifecycleTransition`：生命周期迁移声明。
- `PortLifecycleBoundary`：生命周期边界。
- `PortLifecycleDeclaration`：生命周期声明汇总。

### `envelope.py`

定义通用信封：

- `EnvelopeKind`：信封类型。
- `PortCallMetadata`：端口调用元数据。
- `PortBoundaryContext`：端口边界上下文。
- `PortRequest`：端口请求信封。
- `PortResponse`：端口响应信封。
- `CommandEnvelope`：命令信封。
- `QueryEnvelope`：查询信封。

## 每个端口明确不做什么

本阶段所有对象均不做以下事情：

- 不调用真实文件、网络、数据库、系统命令、模型或工具。
- 不实现调度循环、插件宿主、适配器、审批、授权、风险评分、记忆、检索、学习、自愈算法。
- 不将 Port 设计为大模型直接可见对象。
- 不引入旧能力包链路。
- 不提前实现 Skill 端口、工具端口、模型端口、记忆端口或插件端口。

## 与 L0 的依赖关系

L1 只依赖 Python 标准库与 `tiangong_kernel.l0_primitives`。

已复用的 L0 对象包括：

- `RefId`
- `TypedRef`
- `CoreResult`
- `ResultStatus`
- `CoreError`
- `ErrorSeverity`
- `TraceContext`
- `MetricRef`

未修改任何 L0 源码文件。

## 与 L2-L6 的边界

本阶段为后续层预留通用协议，但不实现后续层职责：

- L2 可引用身份、边界、健康、生命周期、请求响应信封记录生命体状态。
- L3 可引用命令信封、查询信封、边界越界事实、结果对象推进编排。
- L4 可实现端口协议并接入真实适配器，但真实资源逻辑不在 L1。
- L5 可依据端口身份、健康、生命周期管理插件挂载，但插件宿主不在 L1。
- L6 可复用 L1 协议挂载记忆、学习、Skill、工具、情志、自由意志、自愈等子系统，但子系统逻辑不在 L1。

## 测试命令

已执行：

```bash
python3 -m compileall -q tiangong_kernel tests
python3 -m pytest -q tests
python3 -m pytest -q tests/test_l1_no_l2_imports.py
python3 -m pytest -q tests/test_l1_no_third_party_imports.py
python3 -m pytest -q tests/test_l1_no_real_io.py
python3 -m pytest -q tests/test_l1_ports_are_abstract.py
python3 -m pytest -q tests/test_l1_ports_return_core_result.py
python3 -m pytest -q tests/test_l1_uses_l0_primitives.py
python3 -m pytest -q tests/test_l1_no_execution_keywords.py
python3 -m pytest -q tests/test_l1_chinese_docstrings.py
```

## 测试结果

- `python3 -m compileall -q tiangong_kernel tests`：通过，返回码 0。
- `python3 -m pytest -q tests`：通过，`126 passed in 2.40s`。
- `tests/test_l1_no_l2_imports.py`：通过，`1 passed`。
- `tests/test_l1_no_third_party_imports.py`：通过，`1 passed`。
- `tests/test_l1_no_real_io.py`：通过，`1 passed`。
- `tests/test_l1_ports_are_abstract.py`：通过，`1 passed`。
- `tests/test_l1_ports_return_core_result.py`：通过，`2 passed`。
- `tests/test_l1_uses_l0_primitives.py`：通过，`1 passed`。
- `tests/test_l1_no_execution_keywords.py`：通过，`1 passed`。
- `tests/test_l1_chinese_docstrings.py`：通过，`1 passed`。

补充核验：对比原始主体包与开发后项目的 `tiangong_kernel/l0_primitives` 源码目录，排除缓存文件后无差异。

## 修改清单

新增 L1 源码 8 个文件、新增 L1 专项测试 8 个文件、新增本开发日志 1 个文件。

未修改 L0 源码。

## 未做事项

以下内容属于后续阶段，不属于本阶段缺陷：

1. Skill 端口。
2. 工具端口。
3. 工具组端口。
4. 模型端口。
5. 记忆端口。
6. 调度端口。
7. 真实适配器。
8. 插件宿主。
9. 真实文件、网络、数据库、系统命令、模型或工具调用。
10. L2-L6 状态、编排、适配、宿主与子系统逻辑。

## 是否允许进入下一阶段

允许进入 L1 第二阶段。

理由：本阶段目标文件、协议对象、静态边界测试、L0 依赖测试、真实 IO 禁止测试、中文说明测试、全量 tests 均已通过；L0 源码未被修改；未发现阶段越界实现。
