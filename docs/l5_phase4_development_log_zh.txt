天工造物 L5 第四阶段开发日志
阶段：插件生命周期状态机与挂载声明
日期：2026-06-04

一、前置核验
- 已读取第四阶段最终整合版提示词。
- 已从第三阶段完整工程包继续开发。
- 已确认第三阶段可消费对象存在：RegistrySnapshot、RegistryIndex、ConflictReport、PublicProjection、AuditIndex、Delta、Revision。
- 开发前已生成 L0-L4 hash baseline、L5 phase1-phase3 hash baseline、tests inventory baseline。

二、开发范围
- 仅新增 L5 第四阶段不可执行声明模型。
- 未实现真实插件加载、真实挂载、真实启停、真实生命周期执行、真实热切换、真实迁移、真实 replay、真实回滚、真实自愈执行器或 L6 业务插件。
- 未修改 L0-L4。

三、新增核心对象
- PluginLifecycleStateRef / PluginLifecycleTransitionRule / PluginLifecycleStateMachine
- PluginMountDeclaration / PluginMountSurfaceRef
- PluginLifecycleValidationReport / PluginMountDeclarationConflictReport
- PluginLifecycleQualityGateDecision / PluginLifecycleQualityGate
- PluginLifecyclePublicProjection / PluginLifecyclePublicProjectionBuilder
- PluginLifecycleAuditIndex / PluginLifecycleAuditEventRef
- PluginSelfHealingDeclaration / PluginRecoveryPlanDeclaration
- PluginSelfHealingValidationReport / PluginSelfHealingQualityGateDecision

四、共享文件声明性扩展
- __init__.py：增加 L5 phase4 安全导出，保留 phase1-phase3 公开对象。
- invariants.py：增加 L5Phase4InvariantSuite。
- registry_conflict.py：增加第四阶段生命周期、挂载、热切换、迁移、replay、自愈相关 conflict kind。

五、测试结果摘要
- compileall：passed。
- collect-only：1102 tests collected。
- L5 phase4 targeted pytest：50 passed。
- plugin_host 子集：53 passed, 1049 deselected。
- full pytest：1102 passed。
