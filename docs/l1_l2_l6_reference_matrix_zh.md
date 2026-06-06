# 天工造物新版 L1 → L2-L6 引用矩阵（稳定性整修版）

生成时间：2026-06-03

## 1. 矩阵结论

L1 只向后续层提供端口协议、请求/响应对象、边界说明、提示对象和报告对象。L1 不引用 L2-L6，也不实现任何真实外部能力。后续层可引用 L1，但不得反向污染 L1。

## 2. 分层引用规则

| 层级 | 可引用的 L1 内容 | 禁止事项 | 说明 |
|---|---|---|---|
| L2 领域状态层 | PortResult、Envelope、状态连续性端口、候选/验证/变更/实验对象、记忆/上下文/检索协议 | 不得让 L1 import L2；不得把状态机实现下沉到 L1 | L2 可持久化或解释状态，但 L1 只给协议形状。 |
| L3 运行编排层 | Skill、ToolGroup、ToolRelease、ModelEnvelope、ActionEffect、Schedule、Decision、Risk、Policy 等端口 | 不得把调度循环、执行计划、真实任务启动写入 L1 | L3 可编排行动，但必须通过 L1 的边界对象表达输入输出。 |
| L4 外部适配层 | Infrastructure、Content、Communication、Resource、Environment、SecurityBoundary、CompatibilityMigration 等端口 | 不得在 L1 写真实 IO、网络、模型客户端、工具客户端或数据库适配 | L4 负责外部系统适配，L1 只定义适配边界。 |
| L5 插件宿主层 | ComponentRegistry、PluginManifest、PluginLifecycleBoundary、PluginIsolationBoundary 等端口 | 不得在 L1 实现插件加载、扫描目录、动态 import 或插件宿主 | L5 可做插件宿主，L1 只定义插件声明与隔离边界。 |
| L6 子系统插件层 | Learning、SelfLearning、SelfIteration、Evolution、Candidate、Change、Experiment、Validation 等端口 | 不得绕过 Skill 直显、工具组释放和边界层；不得直接修改 L1 协议 | L6 插件可提交候选、证据、验证结果和演化提示，但不能绕过边界合入。 |

## 3. 控制面 / 执行面 / 观察面关系

```text
控制面：policy / risk / decision / control_boundary / schedule / security_boundary
  ↓ 约束
执行面协议：skill / tool / tool_group / tool_binding / tool_release / model_envelope / action_effect
  ↓ 产生观察与证据
观察面：event / observation / metric / audit / feedback / reflection / memory / context / retrieval
  ↓ 汇入横切治理
横切治理：candidate / change / experiment / validation / state_continuity / component_registry / compatibility_migration
```

## 4. 自我学习 / 自我迭代 / 自我进化预留接口

L1 只允许表达以下对象：候选、意图、证据、边界、提示、验证引用、回滚提示、状态连续性引用。L1 不执行学习算法，不自动生成候选，不真实修改 Skill，不真实生产工具，不真实合入候选，不真实回滚。

建议后续层引用路径：

```text
L6 子系统插件提交 LearningCandidate / IterationCandidate / EvolutionCandidate
  → L1 CandidateSource / CandidateEvidence / CandidateBoundary
  → L1 Validation / Verification / Experiment / Change
  → L2 记录状态，L3 编排复核，L4 做外部验证适配，L5 做插件隔离
  → 仍由后续真实边界层决定是否进入执行或合入
```

## 5. `RuntimeContext` 命名说明

`environment_ports.py` 中的 `RuntimeContextPort` 和 `RuntimeContextDeclare*` 仅表示“运行上下文声明协议”。`state_continuity_ports.py` 中的 `RuntimeStateRef` 来自 L0，表示“运行状态引用”。二者都不是旧 Runtime 主循环，也不是新版核心对象；不得据此恢复旧版调度中心。

## 6. `__init__.py` 引用策略

L1 包入口只导出稳定公共骨架。后续层引用具体端口时，应使用子模块显式导入，例如：

```python
from tiangong_kernel.l1_ports.candidate_ports import CandidatePromotionHint
from tiangong_kernel.l1_ports.validation_ports import ValidationRequestPort
```

不建议把所有端口平铺到 `tiangong_kernel.l1_ports` 顶层命名空间。
