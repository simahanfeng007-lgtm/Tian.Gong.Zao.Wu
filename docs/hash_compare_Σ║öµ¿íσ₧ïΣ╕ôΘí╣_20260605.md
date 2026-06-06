# Hash compare（五模型 hotfix3，可复核 zip-to-zip 口径）

## 口径

- compare_kind：zip-to-zip replay for P2-001 baseline correction
- baseline：`天工造物_L5全阶段_hotfix2_五大模型高适配专项修复包_20260605.zip`
- baseline_sha256：`e63227c80f12a2700e56e42a6b1266ce55de43b4abf6c6b540021ee3b93357db`
- current：`天工造物_L5全阶段_hotfix3_五大模型高适配专项修复包_20260605.zip`
- current_sha256：`0a56e4ebf44ed840b615643a68446711d093cde6727c712e2e1bf714527cb409`
- path_normalization：strip first zip root directory; ignore __pycache__ and .pyc

## 统计

- added：28
- removed：20
- modified：9

## L5 影响

- L5 added：[]
- L5 removed：[]
- L5 modified：[]

结论：hotfix3 vs hotfix2 five-model baseline has L5 source 0 added / 0 modified / 0 removed。

## Modified files

- `docs/five_model_provider_factsheets_and_matrices_20260605.json`
- `docs/provider_budget_matrix_20260605.md`
- `docs/provider_capability_matrix_20260605.md`
- `docs/provider_endpoint_matrix_20260605.md`
- `docs/provider_error_taxonomy_matrix_20260605.md`
- `docs/provider_feature_gap_matrix_20260605.md`
- `tiangong_kernel/l1_ports/model_provider_governance_ports.py`
- `tiangong_kernel/l4_action_grounding/__init__.py`
- `tiangong_kernel/l4_action_grounding/model_provider_adapter.py`

## Added files（摘要）

- `docs/L1_L4_修改清单_五模型专项_20260605.md`
- `docs/L5_影响评估_五模型专项_20260605.md`
- `docs/L5_未破坏证明_五模型专项_20260605.md`
- `docs/archived_prompts/天工造物_L5第七阶段开发提示词_20260604_确认修正版.txt`
- `docs/compileall_full_五模型专项_20260605.log`
- `docs/compileall_五模型专项_20260605.log`
- `docs/forbidden_scan_五模型专项_20260605.json`
- `docs/forbidden_scan_五模型专项_20260605.md`
- `docs/hash_compare_五模型专项_20260605.json`
- `docs/hash_compare_五模型专项_20260605.md`
- `docs/pytest_full_best_effort_五模型专项_20260605.log`
- `docs/pytest_guard_subset_五模型专项_20260605.log`
- `docs/pytest_hotfix3_targeted_五模型专项_20260605.log`
- `docs/pytest_五模型专项_20260605.log`
- `docs/五大模型专项交付索引_20260605.md`
- `docs/五大模型专项未做事项_20260605.md`
- `docs/五大模型官方文档factsheet_20260605.md`
- `docs/五大模型高适配专项修复报告_20260605.md`
- `docs/五大模型高适配专项诊断报告_20260605.md`
- `docs/前置材料核对结论_五模型专项_20260605.md`
- `docs/测试结果_五模型专项_20260605.md`
- `tests/test_docs_filenames_are_utf8_readable.py`
- `tests/test_hotfix3_l5_impact_report_matches_hash_compare.py`
- `tests/test_l1_model_invocation_port_exists.py`
- `tests/test_l1_model_provider_port_exists.py`
- `tests/test_l4_model_provider_adapter_public_export_or_handoff.py`
- `tests/test_provider_factsheet_mimo_lowercase_and_api_surfaces.py`
- `tests/test_provider_factsheet_official_doc_refs_match_provider.py`
