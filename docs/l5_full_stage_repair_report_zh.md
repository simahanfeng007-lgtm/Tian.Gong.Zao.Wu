# 天工造物 L5 全阶段 hotfix2 情志专项修复报告

## 1. 修复结论
- 修复状态：已完成 hotfix2 最小补丁。
- 修复对象：L5 插件宿主层情感 / 情志系统基础挂载预留。
- 修复边界：只修改 L5 插件宿主声明层、phase7/phase8 收口、公共投影、L5→L6 handoff、audit index、quality gate 与测试。
- 未修改 L0。
- 未改 L1-L4 核心语义。
- 未实现 L6 情感插件。
- 未实现情感模型、七情六欲算法或情绪驱动执行器。
- 未新增真实工具调用、L4 adapter 调用、文件/网络/终端/数据库/凭据/沙箱访问入口。

## 2. 质检输入风险归并
- 原质检结论：P0=0，P1=0，P2=5，P3=4。
- 本轮必须处理的 L5 P2：
  1. P2-01：情志专项未纳入 L5 final governance matrix / capability readiness matrix。
  2. P2-02：L5→L6 handoff freeze 未单列情感插件禁止误用清单。
  3. P2-03：L5 public projection / audit index 未包含 Affective 摘要与安全审计 refs。
  4. P2-04：缺 L5 情志专项测试。
- 本轮不处理的非 L5 阻断项：P2-05 L1 Affective 端口别名，按质检意见不作为当前 L5 阻断。

## 3. 核心修复内容
### 3.1 L5 情志声明层
新增 `tiangong_kernel/l5_plugin_host/affective_plugin_declaration.py`，提供：
- AffectiveCapabilityDeclaration
- AffectivePluginMountDeclaration
- AffectiveModulationContractBinding
- AffectiveSafetyBoundaryRef
- AffectiveAuditBinding
- AffectivePublicProjectionSummary
- AffectiveL6HandoffRef
- AFFECTIVE_PLUGIN_KIND_REF
- AFFECTIVE_CAPABILITY_KIND_REFS
- AFFECTIVE_MOUNT_KIND_REF
- AFFECTIVE_ALLOWED_MODULATION_REFS
- AFFECTIVE_FORBIDDEN_MISUSE_REFS

上述对象均为声明 / ref / summary，不是执行对象。

### 3.2 Phase7 挂载预留
- 在 phase7 generic plugin host precheck 中加入 AffectivePlugin / AffectiveCapability 行。
- 增加 AffectivePluginMountDeclaration 与 PluginAffectiveMountValidator。
- 约束 Affective mount 不得包含 module_path、import_path、entry_point、callable、handler、endpoint、tool_schema、function_schema、plugin_instance。
- Affective mount scope 固定为 L6 planning only。

### 3.3 Phase8 最终收口
- governance matrix 增加 AffectivePlugin 覆盖行。
- capability readiness matrix 增加 AffectiveModulation / ExpressionStyle / AttentionBias / MemoryWeight / RiskSensitivity / LearningMotivation 等 capability 行。
- final public projection 增加 redacted affective summary refs。
- L5→L6 handoff freeze 增加情志插件禁止误用清单。
- audit index 增加 AffectiveAuditBinding / AffectiveSafetyBoundaryRef / AffectiveL6HandoffRef / AffectivePublicProjectionSummary refs。
- final quality gate 增加情志专项硬门。

### 3.4 测试补丁
新增 8 个测试文件、21 个测试用例，覆盖：
- 情志挂载不可执行。
- 情志插件不得执行工具或调用 L4 adapter。
- 情志调制不是授权。
- 情志不得绕过 Policy / HumanGate / Audit。
- 情志公共投影最小披露。
- 情志 L6 handoff 禁止真实执行。
- 情志只能影响表达、注意力、优先级、记忆权重、风险敏感度、学习动机。
- 情志不得修改核心或提交副作用。

## 4. 验证摘要
- compileall：通过。
- collect-only：1329 collected，exit=0。
- L5 affective targeted：21 passed。
- L5 phase targeted：phase1-phase8 + affective 合计 390 passed。
- plugin host subset：21 passed，1308 deselected。
- full pytest：1329 passed。
- pytest -q：1329 passed。
- forbidden scan：69 source files scanned，blocking_findings=0。
- hash compare：L0-L4 clean；L5 only additive/compatible repair。
- test inventory compare：新增 21，删除 0。
- public export compatibility：删除/重命名 0，新增 17。

## 5. 剩余事项
- 无未修 P0。
- 无未修 P1。
- P2-05：L1 Affective 端口别名仍按后续优化处理，不属于当前 L5 修复阻断。
- P3-01：phase2 独立 quality gate 文件命名统一，仍可后续整理。
- P3-02：phase6 历史 hash compare 文档 pycache 噪声，最终包已确认无 pycache，不阻断。

## 6. 结论
P0/P1 已保持为 0；L5 情志专项 P2-01 至 P2-04 已完成最小补丁修复。当前包具备重新提交 L5 总质检条件。最终是否冻结必须由 L5 总质检员裁决。
