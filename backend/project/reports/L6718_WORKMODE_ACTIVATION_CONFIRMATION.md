# L6718 工作模式激活确认报告

- status: pass
- runtime_tools_after_active_load: 158
- active_assets: 9
- active_learned_tools: 7
- active_learned_skills: 2
- builtin_runtime_skill_files: 8
- direct_calls_pass: 9/9
- no_pollution_pass: True

## Active learned assets
- learned_skill_skill_8f262618 | skill | project_diagnostic | active
- learned_skill_skill_e5ddfa68 | skill | project_diagnostic | active
- learned_tool_r21_doc_skill_production_adapter_beac5ce8 | tool | doc_skill_production | active
- learned_tool_r21_experience_reuse_adapter_2f161b65 | tool | experience_reuse | active
- learned_tool_r21_project_diagnostic_adapter_2036dac3 | tool | project_diagnostic | active
- learned_tool_r21_pure_transform_adapter_0e391b6f | tool | pure_transform | active
- learned_tool_r21_schema_contract_check_adapter_c3f34633 | tool | schema_contract_check | active
- learned_tool_tool_2c55f368 | tool | project_diagnostic | active
- learned_tool_tool_53925862 | tool | project_diagnostic | active

## Verification commands
```bash
PYTHONPATH=. python run_agent.py --mock --tool-mode runtime_governed --workspace . --once "asset-activate status"
PYTHONPATH=. python run_agent.py --mock --tool-mode runtime_governed --workspace . --once "asset-activate smoke 工作模式确认"
PYTHONPATH=. python run_agent.py --mock --tool-mode runtime_governed --workspace . --once "runtime-tools align"
python -m compileall -q tiangong_agent_runtime tiangong_agent_shell .linyuanzhe/active_assets tests
PYTHONPATH=. pytest -q
```
