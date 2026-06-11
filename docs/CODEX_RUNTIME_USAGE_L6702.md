# L6.70.2-CodeX Runtime 可用注册说明

## 结论

Code-X 已从旁路候选进入 v2 Runtime 可调用状态。当前包不是 v1 源码迁移，而是 v2 原生纯净重建注册版。

## 权限口径

- LLM 是主脑、工程判断者、最终裁决者。
- Code-X 是代码执行外骨骼。
- Planner 只做动作建议，不夺权。
- 子代理只做 evidence-only 侦察/测试/审查/迁移/视觉验证，不直接提交主 patch。
- A0-A4 自动放行并审计；A5 硬阻断。

## Runtime 已注册入口

显式命令可通过 `RuntimeEntry.run_text(...)` 或桌面端 Runtime 文本入口触发：

```text
code-x status
code-x smoke .
code-x repo-map .
code-x locate "bug description"
code-x search "symbol or behavior"
code-x pytest tests
code-x quality
code-x snapshot
code-x changed
code-x package src dist/code_x_delivery.zip
code-x tool repo_map {"max_files": 2000}
```

## 直接工具调用

也可通过 `RuntimeEntry.execute_plan(...)` 调用工具：

```python
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation

runtime = RuntimeEntry()
result = runtime.execute_plan([
    ToolInvocation("repo_map", {}),
    ToolInvocation("issue_to_file_localizer", {"issue_text": "import error"}),
    ToolInvocation("workspace_patch_applier", {"edit_units": [
        {"edit_type": "create_file", "path": "src/new_feature.py", "content": "VALUE = 42\n"}
    ]}),
    ToolInvocation("python_quality_runner", {}),
    ToolInvocation("code_x_package_workflow", {"include_paths": ["src"], "output_zip": "dist/code_x_delivery.zip"}),
], workspace="/path/to/workspace")
```

## 验证命令

后端 Runtime 可用性：

```bash
cd backend/project
python3 run_codex_runtime_smoke.py
python3 -m pytest tests/test_codex_runtime_registration.py -q
```

前端 Code-X 投影桥接：

```bash
cd frontend/linyuanzhe_frontend
python3 run_codex_bridge_smoke.py
```

跨平台 launcher：

```bash
./launchers/run_codex_runtime_smoke_l6702.sh
./launchers/run_codex_frontend_bridge_smoke_l6702.sh
```

Windows：

```bat
launchers\run_codex_runtime_smoke_l6702.bat
launchers\run_codex_frontend_bridge_smoke_l6702.bat
```

## 已注册能力层

- 工程感知：repo_map / file_tree_scan / symbol_index / dependency_graph / call_graph / test_map 等。
- 上下文装甲：LINYUANZHE.md 生成、规则读取、上下文压缩、handoff、变更索引。
- 代码定位：issue→文件、文件→符号、符号→行号、语义搜索、失败日志映射、影响范围。
- Patch 生产：patch plan、edit unit、diff、workspace apply、冲突检测、hash、manifest。
- 执行验证：环境探测、命令能力探测、pytest、npm/build/lint/typecheck、静态分析、降级测试策略。
- 失败归因：语法/import/依赖/测试/flaky/timeout/A5 阻断分类与下一轮修复建议。
- Worktree / 回滚 / 打包：snapshot、restore、delivery candidate、zip delivery。
- 子代理：research/test/review/security/refactor/migration/frontend visual，均 evidence-only。

## 无污染边界

- 未复制 v1 源码。
- 未 import v1 模块。
- 未复用 v1 registry / executor / terminal / provider / self-iteration。
- 未替换 v2 ToolRegistry。
- 无 monkey patch。
- 无启动时副作用。
- 无后台常驻 loop。

## R13C 新增 Skill 命令

```text
code-x skill
code-x readiness
code-x v1-audit
code-x fix "问题描述"
```

- `code-x skill`：返回 LLM 使用 Code-X 的默认闭环、recipes 和下一步规则。
- `code-x readiness`：返回世界级代码能力结构评估。
- `code-x v1-audit`：返回 v1 代码链语义导入与其他 v1 工具未导入边界。
- `code-x fix`：生成修复前半链：Skill → 规则 → repo_map → 定位 → snapshot → patch plan。真实写入仍由 LLM 裁决。
