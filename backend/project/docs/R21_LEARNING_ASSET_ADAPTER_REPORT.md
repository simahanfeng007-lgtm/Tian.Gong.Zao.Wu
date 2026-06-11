# L6.70.2 R21 学习资产实用型 Adapter 强化报告

## 结论

R21 在 R20“学习资产受控注册激活可用闭环”上补齐实用型 Adapter 模板层：

```text
学习成功 → R16 契约 → R17 沙箱前置 → R18 候选包 → R19 发布门 → R20 受控激活 → R21 实用型 Adapter → learned_tool_* 可直接干活 → smoke → runtime alignment
```

R21 不是新增审批链，而是让候选 Tool 的 `candidate_adapter_draft(arguments)` 从“元数据返回”升级为“参数内确定性执行”。

## 当前能力

- Runtime 基础工具数：149。
- R21 adapter drill 激活后工具数：154。
- usage card：149 / 149 基础全覆盖；adapter drill 后 learned tools 继续纳入 alignment。
- 新增 5 类 learned tool adapter 模板，每类均有 smoke 示例。
- R21 drill 会生成 5 个 R18 风格候选包，经 R20 激活为 5 个 `learned_tool_*`，并逐个真实调用。
- R20 activation smoke 已升级为按 `adapter_template_id` 使用模板专属样本，避免 schema/diagnostic/doc 类 adapter 被通用样本误判。
- R18/R20 静态契约测试已改为合法 Python，避免 Markdown 写入 `.py` 导致 AST/no-pollution 误报。

## 新增工具

- `learning_asset_adapter_guide`
- `learning_asset_adapter_template_list`
- `learning_asset_adapter_template_normalize`
- `learning_asset_adapter_template_validate`
- `learning_asset_adapter_template_smoke`
- `learning_asset_adapter_drill`

## 新增命令

```text
asset-adapter guide
asset-adapter templates
asset-adapter normalize <template_id>
asset-adapter validate <template_id>
asset-adapter smoke <template_id|all>
asset-adapter drill
runtime-tools tool <learned_tool_name> {json_args}
```

## 五类模板

1. `pure_transform`：JSON 归一化、Markdown 表格、字段提取、正则批检、简单统计、路径过滤。
2. `schema_contract_check`：ToolSpec / SkillSpec / learning_asset_contract / usage card / chain recipe 校验。
3. `project_diagnostic`：只分析输入的测试失败、import error、repo_map、changed_files 摘要，给出 next_action_hint。
4. `doc_skill_production`：生成 SKILL.md、usage card、handoff、release note、工程师接力提示词草案。
5. `experience_reuse`：从 decision_memory / task_digest / handoff_digest 摘要中抽取可复用经验并建议 Tool/Skill 候选。

## 产物链

```text
.linyuanzhe/candidate_sandbox/r18/r21_adapter_templates/
└─ tool_r21_<template>_adapter_<hash>/
   ├─ manifest.json
   ├─ tool_adapter_draft.py
   ├─ static_scan.json
   ├─ smoke_result.json
   ├─ rollback_evidence.json
   ├─ registration_review.json
   ├─ README.md
   ├─ tests/test_static_contract.py
   └─ candidate_package.zip

.linyuanzhe/active_assets/r20/
└─ tool_r21_<template>_adapter_<hash>/
   ├─ activation_manifest.json
   ├─ manifest.json
   ├─ tool_adapter_draft.py
   ├─ rollback_evidence.json
   └─ registration_review.json
```

## 实测结果

- backend compileall：PASS
- frontend/backend compileall：PASS
- pytest：22 passed
- Code-X Runtime smoke：PASS
- R20 activation smoke：PASS
- R21 adapter smoke：PASS；5 templates；5 direct learned tool calls
- runtime-tools alignment：PASS；149 / 149 usage card 全覆盖
- frontend bridge smoke：PASS
- no-pollution AST scan：PASS；977 Python files；0 violations

## 执行边界

- 允许：参数内纯函数转换、schema 校验、输入摘要诊断、文档草案、经验抽取、workspace 内候选/active 证据写入。
- 禁止：触网、shell、后台 loop、凭证读取、workspace 破坏性写入、自动提交、自动替代 LLM 决策、复制/import v1、复用 v1 registry/executor/provider/self-iteration。
- 高权限行为继续走 Code-X / Runtime 既有工具链和 A5 风险判断；R21 adapter 只做 LLM 可控的安全辅助执行。
