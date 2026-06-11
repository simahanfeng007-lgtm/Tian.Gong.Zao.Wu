# L6.70.2 R13C Code-X Skill 使用说明

## 结论

R13C 增补了 LLM 可读的 Code-X 使用 Skill，并把该 Skill 暴露为 Runtime 工具：

- `code_x_skill_guide`
- `code_x_world_class_readiness_check`
- `code_x_v1_import_audit`

## 新增命令

```text
code-x skill
code-x readiness
code-x v1-audit
code-x fix "问题描述"
```

## 用途

- `code-x skill`：让 LLM 主脑读取 Code-X 工具链使用方法。
- `code-x readiness`：确认世界级代码能力结构与仍需实证的缺口。
- `code-x v1-audit`：确认 v1 哪些语义已导入、哪些非代码工具未导入。
- `code-x fix`：生成安全修复前半链：Skill → 规则 → repo_map → 定位 → snapshot → patch plan；真实写入仍由 LLM 裁决后调用 patch 工具。

## R13C1 复检补强

为降低“工具已注册但 LLM 不会稳定选链”的风险，`code_x_skill_guide` 现在额外返回：

- `tool_usage_cards`：关键工具的何时使用、必要输入、输出预期、下一步建议。
- `phase_to_next_action`：start / mapped / located / patched / validation_failed 等阶段到下一工具的确定性提示。
- 补全后的 `command_shortcuts`：包含 `skill` / `readiness` / `v1_audit` / `fix` / `snapshot` / `changed` 等入口。

该补强只增强 LLM 使用说明，不改变 Runtime 权限边界，不写 workspace，不引入 v1 源码或后台 loop。
