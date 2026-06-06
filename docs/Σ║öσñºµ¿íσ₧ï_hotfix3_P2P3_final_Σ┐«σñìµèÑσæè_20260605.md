# 五大模型 hotfix3 P2/P3 final 修复报告（2026-06-05）

## 修复范围

本轮只修第二轮质检报告剩余 P2/P3：

- P2-001：hash compare / L5 影响评估可复核基线口径不一致。
- P2-002：MiMo factsheet 官方引用粒度偏粗。
- P3-001：L5 模型能力治理 schema_version 仍为 hotfix2 字样。
- P3-002：hash compare 一致性测试名称大于实际断言。
- P3-003：GPT-5.5 official_doc_url_ref 可进一步切换到 developers.openai.com 最新文档页。

## 已完成修复

1. 重新生成 `docs/hash_compare_五模型专项_20260605.json/md`，改为可复核 zip-to-zip 口径：五模型 hotfix2 → 原始 hotfix3。
2. 新增 `docs/hash_compare_hotfix3_to_p2p3_final_20260605.json/md`，记录原始 hotfix3 → P2/P3 final 的真实 delta。
3. 修正 `docs/L5_影响评估_五模型专项_20260605.md` 与 `docs/L5_未破坏证明_五模型专项_20260605.md`。
4. MiMo factsheet 追加并引用：model/rate-limits、model release、pay-as-you-go、token plan quick access、token plan price comparison、error codes、model hyperparameters。
5. MiMo factsheet 将 streaming、max output、cache、error code、rate-limit、pricing 从粗粒度 unknown/ref 升级为官方 ref-backed 字段；仍不释放真实 endpoint 给插件。
6. GPT-5.5 official_doc_url_ref 切到 `developers.openai.com/api/docs/models/gpt-5.5`、`developers.openai.com/api/docs/guides/latest-model`、`developers.openai.com/api/docs/pricing`。
7. GPT-5.5 context window 修正为 1,050,000。
8. L5 schema version 统一为 `0.1.hotfix3-p2p3-final-five-model`。
9. `test_hotfix3_l5_impact_report_matches_hash_compare.py` 已改为读取 hash_compare JSON 并验证 L5 added/modified/removed 与文档一致。
10. 新增 `test_l5_model_capability_schema_version_hotfix3_final.py`。

## 测试结果

- compileall：通过。
- P2/P3 targeted：8 passed。
- L4/L5/L6/model/provider 子集：732 passed, 663 deselected。
- full pytest：1395 passed。
- forbidden scan：0 blocking findings。

## 边界确认

本轮未启用 live provider，未新增模型 SDK，未新增 HTTP 调用，未释放 provider base_url 给插件。L6 仍只能声明 `ModelCapabilityRequirement`，真实模型调用仍必须走 L3 编排、L5 permit、L4 provider adapter。

## 建议

建议进入 L6 策划与一般插件开发；不建议直接启用真实模型调用。真实 provider live adapter 需要另开 L5 permit 签发 + L4 live adapter 专项。
