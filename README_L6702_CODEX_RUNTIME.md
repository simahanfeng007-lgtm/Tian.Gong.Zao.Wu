# L6.70.2-CodeX：LLM 代码执行外骨骼 Runtime 可用注册版

本包目标：让 Code-X 不再停留在候选池，而是作为 v2 Runtime 可调用工具链进入临渊者外骨骼。

## 快速验证

Linux/macOS：

```bash
./launchers/run_codex_runtime_smoke_l6702.sh
./launchers/run_codex_frontend_bridge_smoke_l6702.sh
```

Windows：

```bat
launchers\run_codex_runtime_smoke_l6702.bat
launchers\run_codex_frontend_bridge_smoke_l6702.bat
```

## 快速使用

在 Runtime 文本入口中使用：

```text
code-x status
code-x smoke .
code-x repo-map .
code-x locate "import error after refactor"
code-x package src dist/code_x_delivery.zip
```

## 本包状态

- Code-X Runtime 注册：已完成
- PlanBridge 触发：已完成
- 后端真实 smoke：通过
- 前端 Code-X 投影 smoke：通过
- no-pollution：通过

详见：`docs/CODEX_RUNTIME_USAGE_L6702.md`。

## R13C 增补：Code-X Skill 与 v1 导入审计

R13C 在 R13B Runtime 可用注册版基础上增加：

```text
code-x skill
code-x readiness
code-x v1-audit
code-x fix "问题描述"
```

作用：

- `code_x_skill_guide` 让 LLM 主脑读取 Code-X 使用 Skill，避免工具可用但不会选链。
- `code_x_world_class_readiness_check` 区分“结构达到世界级门槛”和“还未跑大型公开 benchmark”。
- `code_x_v1_import_audit` 明确 v1 代码生产链语义已导入，v1 非代码工具未混入 Code-X。

R13C 不复制 v1 源码，不 import v1，不复用 v1 registry/executor/terminal/provider/self-iteration。

## R13C1 复检补强

本复检包在 R13C 基础上补强 LLM 使用 Skill：`code_x_skill_guide` 新增 `tool_usage_cards` 与 `phase_to_next_action`，用于稳定指导 LLM 选工具、接下一步、失败归因和二次修复。该补强不改变权限、不复制 v1、不引入后台 loop。

## R14 / v1 非 Code-X 工具纯净去重导入

本轮把用户补充的 `v1_tools_code_search.zip` 按 v2 边界做去重后加入 Runtime，但不混入 Code-X：

- Code-X 已覆盖的代码生产链、终端执行、Patch、验证、回滚语义：只保留 R13C1，不重复导入。
- 文件读写/传输治理：v2 已有工具与 Code-X 交付链；本轮只补只读 `workspace_text_search`。
- 会话/作业/经验搜索：纯净重建为 `conversation_history_search`、`task_pattern_search`、`experience_mentor_search`。
- 文档提取：纯净重建为 `document_text_extract`，支持 txt/md/json/jsonl/csv/docx/pdf 降级提取。
- 网页可读性：纯净重建为 `web_readability_extract`，仅处理已提供 HTML/正文，不联网抓取。
- 学习精通：纯净重建为 `learning_master_plan`，只做 L1-L5 学习链路规划。
- Tool/Skill 生产：纯净重建为 `tool_skill_blueprint`，只产出草案、测试矩阵和候选建议，不注册、不执行。
- 截图视觉、真实联网搜索、桌面外设：暂缓到独立系统，避免伪造能力。

新增 Runtime 文本命令：

```text
v1-import status
v1-import audit
v1-import guide
v1-import search "关键词"
v1-import conversation "上次讨论"
v1-import task "相似任务"
v1-import experience "经验关键词"
v1-import document docs/a.docx
v1-import readability "<html>..."
v1-import learning "学习目标"
v1-import tool-skill "生产目标"
```

污染边界：未复制 v1 源码，未 import v1，未复用 v1 registry/executor/provider/self-iteration，未启动后台 loop，Planner/子代理不夺权。

## R15：全局工具注册表 / Skill / LLM 实操对齐

新增命令：

```bash
runtime-tools align
runtime-tools drill
runtime-tools tool <tool_name> {json_args}
```

用途：

- `runtime-tools align`：生成 127 个 Runtime 工具的 LLM usage cards，检查注册表、风险分级、Skill 来源和无污染边界。
- `runtime-tools drill`：模拟 LLM 从用户意图进入 PlanBridge，再路由到 Runtime 工具名，确认无空路由、无缺失工具。
- `runtime-tools tool <tool_name> {json_args}`：LLM 明确选择任意已注册工具时，通过 Runtime 审计链调用。

R15 复检结果：127 个工具 / 127 张 usage card / 29 个 LLM 路由场景 / 19 组代表性真实执行链全部通过。

## R18 Tool/Skill 候选包生产沙箱

R18 在 R17 沙箱前置对齐后，新增真实候选包生产沙箱：

- `learning_asset_candidate_sandbox_guide`
- `learning_asset_candidate_sandbox_build`
- `learning_asset_candidate_sandbox_validate`
- `learning_asset_candidate_sandbox_review`

CLI 入口：

```bash
asset-candidate-sandbox guide
asset-candidate-sandbox build "pytest missing tests"
asset-candidate-sandbox validate
asset-candidate-sandbox review
asset-candidate-sandbox drill "pytest missing tests"
```

边界：只在 `.linyuanzhe/candidate_sandbox/r18` 下写候选包、扫描、smoke、回滚、审阅证据；不注册、不激活、不调用候选工具、不导入 v1、不启动后台 loop。

