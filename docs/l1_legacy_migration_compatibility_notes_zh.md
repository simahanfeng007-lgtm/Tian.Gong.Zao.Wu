# 天工造物新版 L1 旧架构迁移兼容说明（稳定性整修版）

生成时间：2026-06-03

## 1. 结论

新版 L1 不恢复旧能力包体系，不恢复旧 Runtime 主循环，不以“神枢”作为新版核心对象。L1 的职责是端口协议层：定义边界、请求、响应、提示、报告和引用形状，为 L2-L6 提供稳定协议。

## 2. 旧概念处理表

| 旧概念 | 新版 L1 处理方式 | 禁止事项 |
|---|---|---|
| AbilityPackage / 能力包 | 不恢复；新版以 Skill 作为大模型行动入口，ToolGroup 作为工具组视图 | 不新增 AbilityPackage、AbilityRouter、AbilityExecutor、AbilityPackagePort |
| CapabilityPort | 不恢复；如需能力表达，由 Skill / ToolGroup / ToolRelease / Candidate 等端口组合表达 | 不新增 CapabilityPort 或兼容外壳 |
| 旧 Runtime 主循环 | 不恢复；L1 只保留运行上下文和状态引用协议 | 不在 L1 写 run loop、真实调度器或执行计划器 |
| 旧工具直连执行 | 不恢复；L1 只定义 ToolInvocationIntent / ToolReleaseView 等协议 | 不调用工具、不授予真实执行权 |
| 旧插件加载 | 不恢复；L1 只定义 PluginManifest / PluginLifecycleBoundary / PluginIsolationBoundary | 不扫描目录、不动态导入、不加载插件 |
| 旧自我迭代合入链 | 不恢复；L1 只定义候选、变更、验证、回滚提示 | 不自动合入、不真实回滚、不真实修改 Skill |

## 3. Skill 直显兼容口径

新版主链为：

```text
模型看到 Skill
  → 选择 Skill
  → 后续层做边界裁决
  → 释放 ToolGroup 视图
  → 模型按协议提交工具调用意图
  → 后续真实执行层处理副作用与审计
```

L1 只覆盖上述链条中的协议对象，不实现裁决、释放、调用或审计落盘。

## 4. 候选晋升兼容口径

`candidate_ports.py` 中的 `CandidatePromotionHint` 是统一候选生命周期提示，必须同时承载：

- `learning_candidate`
- `iteration_candidate`
- `evolution_candidate`
- `candidate_ref`
- `validation_refs`
- `verification_refs`

本次稳定性整修已修复同模块重复定义覆盖问题，避免自我迭代 / 自我进化候选字段在运行时丢失。

## 5. 迁移边界

旧项目若迁移到新版，应先映射为 Skill、ToolGroup、Candidate、Change、Experiment、Validation 等协议对象。迁移过程不得把旧实现直接搬入 L1，也不得通过 L1 触发真实 IO、真实模型调用、真实工具调用、真实插件加载或真实状态修改。
