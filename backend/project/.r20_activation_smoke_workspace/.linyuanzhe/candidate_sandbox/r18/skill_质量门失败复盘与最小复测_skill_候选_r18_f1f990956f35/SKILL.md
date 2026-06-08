# 质量门失败复盘与最小复测_skill_候选 候选 Skill 草案

## 状态

候选。不得写入正式 Skill 注册表，不得激活，不得释放能力句柄。

## 用途

把缺失测试、pytest 失败、compileall 失败转化为可执行前的修复/复测策略。

## 触发规则

- 质量门 fail/warn、诊断出现 missing_tests、pytest_missing 或 quality_check_failed。

## 使用链路

- review draft
- check trigger
- map to Runtime tool cards
- execute governed chain
- record outcome

## 禁止边界

- 不得自动注册或激活。
- 不得绕过质量门、发布门、回滚证据和审计。
- 不得导入或复制 v1 源码。
- 不得调用模型、网络、shell 或候选工具。
