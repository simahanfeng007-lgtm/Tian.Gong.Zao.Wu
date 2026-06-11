# L6721 前端修复与生物动态模型增强

## 范围
- 接续 L6719 入口/编码/启动健壮修复包。
- 合入 L6720 前端审查修复：拆分 `main_window.py`、placeholder 动态隐藏、清屏按钮、设置保存反馈、版本常量、停止/复位按钮接线、流式刷新粒度提升。
- 根据 L6_71 全系统动态公式审计，新增 runtime 外壳层生物动态数学底座。

## 生物动态模型底座
新增：`backend/project/tiangong_agent_runtime/biodynamic_policy_core.py`

核心公式：
- `BioDynamicState.load`：资源、失败、不确定性、隐私、污染、冲突、疲劳的加权 allostatic load。
- `BioDynamicState.adaptive_drive`：任务驱动、用户意图、恢复力、可逆性的连续驱动力。
- `evidence_accumulation`：证据积累 + 驱动 + 恢复力 - 压力 - 惯性。
- `dynamic_threshold`：压力升高则阈值更谨慎；驱动/恢复力升高则低摩擦。
- `activation_probability`：把离散 if 门控转成连续激活概率。

## 已动态化的重灾区
- `memory_write_filter.py`：证据数、置信度、隐私、污染、冲突、L5 敏感度均改为动态阈值。
- `forgetting_review_router.py`：用户遗忘信号、隐私抑制、压缩、归档、降级、L5 保护冲突均改为动态阈值。
- `memory_math_core.py`：召回入上下文、review_only、晋升、滞后确认、遗忘复核、状态转移均改为动态公式。
- `execution_policy.py` / `permit_gateway.py`：A0-A4 改为 BioDynamicState 决策；A5 保持硬边界。
- `execution_exoskeleton.py`：输入/输出/smoke 推断从中文关键词 if 链改为连续 lexical biomarker activation。
- `governance_execution.py`：快车道从固定声明改为含动态激活分数与适配阈值。
- `lifecycle_coordinator.py`：自由意志 lease 的时长、预算、步数由动态公式生成。

## 不改原则
- 不修改 L0 内核原语硬约束。
- 不把 A5 硬边界动态化。
- 不引入后台 loop。
- 不引入 v1 import。
- 不让 Planner / 子智能体夺权。
- 不降低 LLM 执行力。

## 验证
- `compileall` PASS
- `pytest` 27 passed
- Code-X Runtime smoke PASS
- R20 activation smoke PASS
- R21 adapter smoke PASS
- runtime tools alignment PASS
- frontend bridge smoke PASS
- cross-platform desktop audit PASS
- workmode activation check PASS：158 tools / 158 usage cards / 9 active assets
