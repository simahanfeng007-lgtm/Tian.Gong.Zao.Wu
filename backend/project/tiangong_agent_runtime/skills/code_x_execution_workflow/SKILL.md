---
name: skill.code_x_execution_workflow
description: 当用户要求代码修复、bug 定位、新功能、重构、跑测试、失败归因、二次修复、回滚、打包交付或长链代码任务时启用。该 Skill 教 LLM 主脑按 Code-X 工具链使用临渊者代码执行外骨骼；不让 Planner 或子代理夺权。
---

# Code-X：LLM 代码执行外骨骼使用 Skill

## 固定角色

- LLM = 主脑、工程判断者、意图源、最终裁决者。
- Code-X = 代码执行外骨骼装甲，负责读库、定位、patch、测试、归因、回滚、交付。
- Planner = 动作建议器，只能建议下一步。
- 子代理 = evidence-only 侦察、测试设计、审查、迁移、前端视觉验证；不得直接提交主 patch。

## 默认闭环

任何代码任务按这条链执行：

1. `code_x_skill_guide`：加载当前工作流说明。
2. `project_rules_reader`：读取项目规则。
3. `repo_map`：压缩理解仓库结构。
4. `issue_to_file_localizer` / `semantic_code_search`：定位相关文件。
5. `file_to_symbol_localizer` / `symbol_to_line_localizer`：定位符号与行号。
6. `workspace_snapshot`：写入前创建快照。
7. `patch_plan_generator`：生成 patch 计划。
8. `edit_unit_planner`：拆分 edit unit。
9. `conflict_detector`：检查冲突、路径、覆盖风险。
10. `unified_diff_generator`：给 LLM 审阅 diff。
11. `workspace_patch_applier`：写入 workspace。
12. `python_quality_runner` / `pytest_runner` / `npm_test_runner` / `build_runner` / `lint_runner` / `typecheck_runner`：验证。
13. 验证失败时：`failure_attribution_analyzer` → `repair_loop_planner` → `next_patch_generator` → 回到第 7 步。
14. 成功或阻断时：`changed_files_index` → `handoff_digest` → 必要时 `delivery_candidate_packager` / `zip_delivery_packager`。

## 常用命令

```text
code-x status
code-x skill
code-x readiness
code-x v1-audit
code-x smoke .
code-x repo-map .
code-x locate "报错日志或问题描述"
code-x fix "问题描述"
code-x quality
code-x pytest tests
code-x package src dist/code_x_delivery.zip
code-x tool <tool_name> {json_args}
```

## 任务类型 recipes

### bug 修复

`code_x_skill_guide → project_rules_reader → repo_map → issue_to_file_localizer → file_to_symbol_localizer → symbol_to_line_localizer → workspace_snapshot → patch_plan_generator → edit_unit_planner → conflict_detector → workspace_patch_applier → python_quality_runner/pytest_runner → failure_attribution_analyzer(失败时) → handoff_digest`

### import 错误

`repo_map → test_failure_trace_mapper → import_error_analyzer → issue_to_file_localizer → affected_area_detector → workspace_snapshot → patch_plan_generator → workspace_patch_applier → python_quality_runner → pytest_runner → handoff_digest`

### 新功能

`project_rules_reader → repo_map → semantic_code_search → affected_area_detector → test_design_subagent → workspace_snapshot → patch_plan_generator → workspace_patch_applier → pytest_runner/build_runner → review_subagent → handoff_digest`

### 多文件重构

`repo_map → dependency_graph → call_graph → affected_area_detector → refactor_review_subagent → workspace_snapshot → patch_plan_generator → workspace_patch_applier → pytest_runner/build_runner/typecheck_runner → changed_files_index → handoff_digest`

### 前端视觉任务

`repo_map → stack_detector → semantic_code_search → frontend_visual_subagent → test_design_subagent → workspace_snapshot → patch_plan_generator → workspace_patch_applier → npm_test_runner/build_runner/lint_runner → frontend_visual_subagent → handoff_digest`

## 下一步提示规则

- 工具返回 `next_action_hint` 时，优先按其建议推进，但 LLM 必须裁决。
- 验证失败不停止，必须进入归因。
- 普通任务最多 3 轮 repair loop；长链任务最多 6 轮。
- 超限后输出阻断原因、已改文件、测试结果、下一步建议。
- 回滚、handoff、状态恢复、续租永不锁死。

## 风险边界

- A0-A4 默认允许并审计。
- A5 必须硬阻断：密钥泄露、代码外传、大规模删除、系统目录破坏、生产环境修改、恶意命令。
- 不复制 v1 源码，不 import v1，不复用 v1 registry/executor/terminal/provider/self-iteration。

## 关键工具使用卡（LLM 选链最小集）

| 工具 | 何时使用 | 必要输入 | 下一步 |
|---|---|---|---|
| `project_rules_reader` | 真实仓库任务开始前读取项目规则 | `repo_root` | `repo_map` |
| `repo_map` | 首次理解仓库、定位前、重构前 | `workspace_root` | `issue_to_file_localizer` / `semantic_code_search` |
| `issue_to_file_localizer` | 由 bug/需求/报错定位候选文件 | `issue_text` | `file_to_symbol_localizer` |
| `semantic_code_search` | 行为语义明确但文件未知 | `query` | `affected_area_detector` |
| `workspace_snapshot` | 任何写入前必须调用 | 可选 `label` | `patch_plan_generator` |
| `patch_plan_generator` | 写入前生成可审阅 patch 计划 | `issue` / 可选 `target_files` | `edit_unit_planner` |
| `edit_unit_planner` | 把计划拆成可执行 edit_units | `patch_plan` | `conflict_detector` |
| `conflict_detector` | 写入前检查覆盖/路径/冲突 | `edit_units` | `unified_diff_generator` / `workspace_patch_applier` |
| `workspace_patch_applier` | LLM 裁决后真实写入 workspace | `edit_units` | `python_quality_runner` / `pytest_runner` |
| `python_quality_runner` | Python patch 后基础验证 | 可选 `target` | `pytest_runner` 或 `failure_attribution_analyzer` |
| `pytest_runner` | 存在 pytest 或用户要求跑测试 | 可选 `test_path` | 失败走 `failure_attribution_analyzer` |
| `failure_attribution_analyzer` | 任意验证失败后必须归因 | `log_text` | `repair_loop_planner` |
| `repair_loop_planner` | 归因后规划二次修复/降级/回滚 | `failure_analysis` / `attempt` | `next_patch_generator` |
| `restore_checkpoint` | patch 错误、阻断、用户要求回滚 | `snapshot_id` | `handoff_digest` |
| `handoff_digest` | 完成/失败/超轮次/新窗口交接 | `task` / `results` | 必要时 `zip_delivery_packager` |
| `zip_delivery_packager` | 用户要求阶段 zip 或交付包 | `include_paths` / `output_zip` | `handoff_digest` |

## 阶段到下一步规则

- `start` → `project_rules_reader`
- `rules_read` → `repo_map`
- `mapped` → `issue_to_file_localizer`
- `located` → `workspace_snapshot`
- `snapshot_ready` → `patch_plan_generator`
- `planned` → `edit_unit_planner`
- `edit_units_ready` → `conflict_detector`
- `conflict_clear` → `workspace_patch_applier`
- `patched` → `python_quality_runner`
- `validation_failed` → `failure_attribution_analyzer`
- `failure_attributed` → `repair_loop_planner`
- `validated` → `changed_files_index`
- `ready_to_deliver` → `handoff_digest`

