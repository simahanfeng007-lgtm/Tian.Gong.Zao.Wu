---
name: skill.v1_clean_import_workflow
description: 当用户要求把 v1 工具、历史会话、作业搜索、经验材料、文档提取、学习精通、Tool/Skill 生产语义去重后加入 v2 时启用。该 Skill 只允许 v2-native 纯净重建，不复制 v1 源码，不 import v1，不混入 Code-X。
---

# v1 非 Code-X 工具纯净去重导入 Skill

## 固定边界

- LLM = 主脑、最终裁决者。
- 本 Skill 只提供只读检索、文档提取、学习规划、Tool/Skill 草案和 next_action_hint。
- Code-X 仍只负责代码执行外骨骼；不要把搜索、学习、文档、截图、工具生产强塞进 Code-X。
- 不复制 v1 源码，不 import v1，不复用 v1 registry/executor/terminal/provider/self-iteration，不启动后台 loop。

## 常用命令

```text
v1-import status
v1-import audit
v1-import guide
v1-import search "关键词"
v1-import conversation "上次/之前/某任务"
v1-import task "类似历史任务"
v1-import experience "经验或 Skill 关键词"
v1-import document docs/example.md
v1-import readability "<html>...</html>"
v1-import learning "学习目标"
v1-import tool-skill "工具或 Skill 生产目标"
```

## 默认链路

1. `v1_clean_import_audit`：先确认去重决策和无污染状态。
2. `v1_clean_import_guide`：加载 LLM usage cards。
3. 按目标选择：
   - 文档/材料搜索：`workspace_text_search → document_text_extract`
   - 上下文续接：`conversation_history_search → task_pattern_search`
   - 经验复用：`experience_mentor_search → learning_master_plan`
   - 学习精通：`learning_master_plan → tool_skill_blueprint(仅 L5/资产化时)`
   - Tool/Skill 生产：`tool_skill_blueprint → queue_skill_candidates/queue_tool_production_requests`
4. 所有工具只返回 evidence、summary、next_action_hint；是否执行下一步由 LLM 决定。

## 去重规则

- v1 代码生产链：已去重到 Code-X，不再导入。
- v1 文件写入/终端/回滚：已由 v2 Runtime 和 Code-X 接管，不再导入。
- v1 自我迭代/心流/主动驱动：已去重到 v2 生命周期系统，不导入 loop。
- v1 搜索/文档/学习/经验/ToolSkill 语义：按独立纯净层重建。
- v1 网页真实联网搜索、截图视觉：暂缓到独立 Provider/前端桌面系统，不能伪造能力。

## 使用判断

- 用户问代码修复、测试、构建、patch、回滚、交付：用 Code-X Skill。
- 用户问 v1 工具融合、历史任务、经验搜索、文档提取、学习精通、Tool/Skill 生产草案：用本 Skill。
- 用户要求把 v1 代码直接搬进 v2：拒绝复制源码，改走语义提炼与纯净重建。
