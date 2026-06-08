# 临渊者 FE01 STEP31Q / L6721 修复报告

## 结论
已确认两类问题：

1. L6719 前端审查建议中的 9 项问题基本存在，已完成 UI 层修复。
2. L6_71 全系统动态公式审计方向成立：记忆、遗忘、执行力、治理、生命周期存在明显固定阈值/硬编码门控。已完成第一轮重灾区动态数学化改造。

## 前端修复
- `main_window.py` 从 3198 行单体拆分为：
  - `main_window.py`
  - `main_window_chat_runtime.py`
  - `main_window_feature_pages.py`
  - `main_window_actions.py`
- 删除/消解未读取的 `_last_*_error` 死字段，统一走 `_record_ui_warning`。
- `_request_task_stop` / `_request_task_reset` 已接入按钮，不再是死方法。
- placeholder 绑定 `<Key>` / `<<Modified>>`，输入后隐藏，空输入恢复。
- 流式刷新间隔压到 24ms，提高逐字/增量观感。
- 设置页保存 Key 后在输入框附近显示 `✓ 已保存` 临时反馈。
- 新增“清屏”按钮，仅清除前端本地渲染，不提交 Runtime。
- 删除 `_submit_confirmation` 无意义别名。
- 版本信息集中到 `version_info.py` / `VERSION_FE01.txt`。

## 生物动态模型增强
新增：`backend/project/tiangong_agent_runtime/biodynamic_policy_core.py`

核心模型：
- `BioDynamicState.load`：资源、失败、不确定、隐私、污染、冲突、疲劳构成 allostatic load。
- `BioDynamicState.adaptive_drive`：任务驱动、用户意图、恢复力、可逆性构成执行驱动力。
- `evidence_accumulation`：模拟连续证据积累，减少纯 if/else 门控。
- `dynamic_threshold`：压力升高时更谨慎，驱动/恢复力升高时降低治理摩擦。
- `activation_probability`：把离散硬门转为连续激活概率。

## 已修复的审计重灾区
- `memory_write_filter.py`：证据数、置信度、隐私、污染、冲突、L5 敏感度动态化。
- `forgetting_review_router.py`：用户遗忘、隐私抑制、压缩、归档、降级、L5 保护动态化。
- `memory_math_core.py`：召回、review_only、晋升、滞后确认、遗忘、状态转移动态化。
- `execution_policy.py` / `permit_gateway.py`：A0-A4 改为动态执行策略；A5 保持硬边界。
- `execution_exoskeleton.py`：输入/输出/smoke 推断从关键词 if 链改为 lexical biomarker activation。
- `governance_execution.py`：快车道增加动态激活分数和适应阈值。
- `lifecycle_coordinator.py`：自由意志 lease 的时长、预算、步数由动态公式生成。

## 保留硬边界
以下内容没有动态化：
- L0 内核原语约束。
- A5 极高危硬阻断。
- 凭证、敏感路径、危险命令、v1 源码/import/registry/executor/provider/self-iteration 复用禁区。
- 后台 loop 禁区。

原因：这些不是“行为策略”，而是系统生存边界；动态化会削弱安全与稳定性。

## 验证结果
- `compileall`：PASS
- `pytest`：27 passed
- Code-X Runtime smoke：PASS
- R20 activation smoke：PASS
- R21 adapter smoke：PASS
- Runtime tool alignment：PASS
- Frontend bridge smoke：PASS
- Workmode activation check：PASS
  - Runtime tools：158
  - usage cards：158 / 158
  - active learned assets：9
- Cross-platform desktop audit：PASS

## 未做事项
- Windows 真机 GUI 点击验收未在当前 Linux 沙箱执行。
- 动态公式第二轮可继续覆盖更深层风险分类器、预算账本和 Provider 调度，但本轮已完成用户点名的重灾区首轮修复。
