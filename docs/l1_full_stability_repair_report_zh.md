# 天工造物新版 L1 全阶段稳定性整修报告

生成时间：2026-06-03  
修复身份：L1 全阶段修复员  
修复范围：只根据第一次总质检报告处理 L1 第 1-8 阶段问题；不进入 L2-L6；不修改 L0；不恢复旧能力包体系。

---

## 1. 修复一句话结论

本次稳定性整修已修复冻结前必须处理的 P1：`candidate_ports.py` 中 `CandidatePromotionHint` 重复定义覆盖问题；已补关键测试与端口索引文档；完整 `compileall` 与完整 `pytest` 通过，建议进入二次质检，二次质检通过后再冻结 L1。

---

## 2. 输入文件清单

| 类型 | 文件 | 说明 |
|---|---|---|
| L1 第 8 阶段交接包 | `/mnt/data/天工造物_L1_第8阶段_交接包_20260603.zip` | 已解压到独立修复工作目录。 |
| 第一次总质检报告 | `/mnt/data/l1_full_quality_audit_report_zh.md` | 已复制到 `docs/l1_full_quality_audit_report_zh.md`。 |
| 修复员提示词 | `/mnt/data/天工造物_L1全阶段修复员提示词_20260603.txt` | 已复制到 `docs/天工造物_L1全阶段修复员提示词_20260603.txt`。 |

原始交接包 SHA256：

```text
bdcca1253c4b05106aac6cd18cfb8ed1a8923cffe2040ff5f48f9e489feaf9d0  /mnt/data/天工造物_L1_第8阶段_交接包_20260603.zip
```

---

## 3. 使用的质检报告

使用报告：`docs/l1_full_quality_audit_report_zh.md`。

报告结论：不建议冻结 L1，应先进入修复阶段。报告列出：P0=0、P1=1、P2=8、P3=4。

---

## 4. P0 修复清单

P0 数量：0。未发现 P0，无需修复。

---

## 5. P1 修复清单

### P1-01：`CandidatePromotionHint` 重复定义覆盖

修复文件：`tiangong_kernel/l1_ports/candidate_ports.py`

修复内容：

1. 删除同模块第二个重复的 `CandidatePromotionHint` 定义。
2. 合并字段，保留统一候选晋升对象需要的完整形状：
   - `candidate_ref: ResourceRef`
   - `learning_candidate: LearningCandidate | None`
   - `iteration_candidate: IterationCandidate | None`
   - `evolution_candidate: EvolutionCandidate | None`
   - `validation_refs: tuple[ValidationRef, ...]`
   - `verification_refs: tuple[VerificationRef, ...]`
   - `schema_version: str`
3. 保持 `candidate_ref` 为统一候选主引用的必填字段。
4. 保持 L1 协议层边界：只表达候选晋升提示，不真实晋升、不合入、不修改系统。

结果：已修复。

---

## 6. P2 修复 / 收口清单

| 编号 | 处理结果 | 说明 |
|---|---|---|
| P2-01 | 文档收口 | `validation_ports.py` 与 `candidate_ports.py` 跨模块同名 `CandidatePromotionHint*` 保留；已在 `docs/l1_total_port_index_zh.md` 中明确前者偏验证链输出提示，后者偏统一候选生命周期提示。 |
| P2-02 | 已修复 | 新增 `tests/test_l1_no_duplicate_public_class_names.py` 与 `tests/test_l1_phase8_candidate_promotion_hint_shape.py`。 |
| P2-03 | 已收口 | 更新 `tiangong_kernel/l1_ports/__init__.py` 顶部说明，并在总端口索引中明确稳定骨架导出策略。 |
| P2-04 | 文档收口 | 在 `docs/l1_total_port_index_zh.md` 中补充 `describe_*`、`request_*`、`submit_*`、`declare_*`、`reference_*` 动词口径。 |
| P2-05 | 文档收口 | 在 `docs/l1_total_port_index_zh.md` 中明确候选继续使用 L0 `ResourceRef`，本次不新增 L0 `CandidateRef`。 |
| P2-06 | 文档收口 | 在 `docs/l1_total_port_index_zh.md` 中补充 Candidate / Change / Experiment / Validation 层级关系。 |
| P2-07 | 已修复 | 新增 `docs/l1_total_port_index_zh.md`、`docs/l1_l2_l6_reference_matrix_zh.md`、`docs/l1_legacy_migration_compatibility_notes_zh.md`。 |
| P2-08 | 部分收口 | 本轮输入未提供侧载同名日志原件，无法做内容级合并；最终交接包统一以 `project/docs/` 内文档为准，并在修复报告中记录该限制。 |

---

## 7. P3 修复 / 收口清单

| 编号 | 处理结果 | 说明 |
|---|---|---|
| P3-01 | 已修复 | `design/` 下乱码长文件名已重命名为正常中文文件名；根目录两份乱码 / sanitized 报告已移入 `docs/` 并使用正常文件名。 |
| P3-02 | 已收口 | `docs/l1_total_port_index_zh.md` 与 `docs/l1_l2_l6_reference_matrix_zh.md` 已说明 `RuntimeContextPort` / `RuntimeStateRef` 不是旧 Runtime 主循环。 |
| P3-03 | 未展开修复 | 大面积重写第八阶段所有端口 docstring 会扩大改动面；本次只修复 P1 所在对象 docstring。建议二次质检后按文档风格专项处理。 |
| P3-04 | 未展开修复 | 测试 helper 抽取属于整洁重构，不影响冻结前边界正确性；本次避免扩大测试结构改动。 |

---

## 8. 未修复项与原因

1. P2-08：未收到侧载 `l1_phase8_development_log_zh.md` 与 `l1_phase8_closure_report_zh.txt` 原件，无法做内容级合并；最终包以 `project/docs/` 为唯一归档源。
2. P3-03：未批量改写端口 docstring，避免无必要扩大源码改动面。
3. P3-04：未抽取测试扫描 helper，避免无必要重构测试结构。
4. 独立 L0 最终归档包 hash 比对：用户本轮未提供独立 L0 最终归档包；本次完成的是“原始 L1 交接包内 L0 与修复后 L0”的 hash 对比，结果无变化。

---

## 9. 修改文件清单

- `tiangong_kernel/l1_ports/candidate_ports.py`
- `tiangong_kernel/l1_ports/__init__.py`
- `docs/l1_phase8_development_log_zh.md`
- `docs/l1_phase8_closure_report_zh.txt`
- `docs/l1_stability_repair_pending_zh.md`

---

## 10. 新增文件清单

- `tests/test_l1_no_duplicate_public_class_names.py`
- `tests/test_l1_phase8_candidate_promotion_hint_shape.py`
- `docs/l1_full_quality_audit_report_zh.md`
- `docs/天工造物_L1全阶段修复员提示词_20260603.txt`
- `docs/l1_total_port_index_zh.md`
- `docs/l1_l2_l6_reference_matrix_zh.md`
- `docs/l1_legacy_migration_compatibility_notes_zh.md`
- `docs/l1_repair_compileall.log`
- `docs/l1_repair_pytest_full.log`
- `docs/l1_repair_pytest_required_group.log`
- `docs/l1_repair_l0_hash_compare.txt`
- `docs/l0_phase1_handoff_report_zh.txt`（由根目录乱码文件名整理而来）
- `docs/l0_phase5_handoff_report_zh.txt`（由根目录 sanitized 文件名整理而来）
- `design/天工造物_L0零依赖原语层设计_v0.1.txt`（由乱码文件名整理而来）
- `design/天工造物_全局架构宪法_v0.1.txt`（由乱码文件名整理而来）

---

## 11. 删除 / 重命名文件清单

以下为文件名整理，不是内容删除：

- `design/╧â...L0..._v0.1.txt` → `design/天工造物_L0零依赖原语层设计_v0.1.txt`
- `design/╧â...全局..._v0.1.txt` → `design/天工造物_全局架构宪法_v0.1.txt`
- `╧â...L0...阶段1..._20260603.txt` → `docs/l0_phase1_handoff_report_zh.txt`
- `sanitized_long_filename_ee371242e542.txt` → `docs/l0_phase5_handoff_report_zh.txt`

---

## 12. 新增端口清单

本次未新增业务端口类。只修复已有 `CandidatePromotionHint` 协议对象，新增测试与文档。

---

## 13. 新增测试清单

1. `tests/test_l1_no_duplicate_public_class_names.py`
   - 目的：AST 检查同一 L1 模块不得重复定义公开顶层类，防止后定义覆盖前定义。
2. `tests/test_l1_phase8_candidate_promotion_hint_shape.py`
   - 目的：确认统一候选晋升提示保留学习、迭代、进化三类候选字段，并确认请求 payload 指向修复后的统一对象。

---

## 14. L0 是否修改

未修改。

补充验证：已从原始 L1 第 8 阶段交接包重新解压一份原始工程，并对比 `tiangong_kernel/l0_primitives/*.py` hash。

结果：

```text
orig files: 58
new files: 58
missing: []
added: []
changed: []
```

---

## 15. 是否 import L2-L6

未发现。

完整测试与必测集合已覆盖 `tests/test_l1_no_l2_imports.py`。

---

## 16. 是否引入第三方库

未发现。

完整测试与必测集合已覆盖 `tests/test_l1_no_third_party_imports.py`。

---

## 17. 是否存在真实 IO / 模型 / 工具 / 插件实现

未发现。

完整测试与必测集合已覆盖：

- `tests/test_l1_no_real_io.py`
- `tests/test_l1_no_execution_keywords.py`
- 各阶段专项测试中的禁止项扫描

---

## 18. 测试命令

```bash
python3 -m compileall -q tiangong_kernel tests
python3 -m pytest -q tests
python3 -m pytest -q \
  tests/test_l1_no_l2_imports.py \
  tests/test_l1_no_third_party_imports.py \
  tests/test_l1_no_real_io.py \
  tests/test_l1_ports_are_abstract.py \
  tests/test_l1_ports_return_core_result.py \
  tests/test_l1_uses_l0_primitives.py \
  tests/test_l1_no_execution_keywords.py \
  tests/test_l1_chinese_docstrings.py \
  tests/test_l1_no_duplicate_public_class_names.py \
  tests/test_l1_phase8_validation_ports.py \
  tests/test_l1_phase8_schedule_ports.py \
  tests/test_l1_phase8_state_continuity_ports.py \
  tests/test_l1_phase8_action_effect_ports.py \
  tests/test_l1_phase8_security_boundary_ports.py \
  tests/test_l1_phase8_component_registry_ports.py \
  tests/test_l1_phase8_compatibility_migration_ports.py \
  tests/test_l1_phase8_candidate_ports.py \
  tests/test_l1_phase8_candidate_promotion_hint_shape.py \
  tests/test_l1_phase8_change_ports.py \
  tests/test_l1_phase8_experiment_ports.py
```

---

## 19. 测试结果

| 命令 | 结果 |
|---|---|
| `python3 -m compileall -q tiangong_kernel tests` | 通过，无错误输出。 |
| `python3 -m pytest -q tests` | `326 passed in 7.59s` |
| L1 必测 + 第八阶段专项 + 新增测试集合 | `63 passed in 5.22s` |

说明：一次“逐文件循环运行”在 `tests/test_l1_ports_are_abstract.py` 前后被外层命令超时打断；随后改用必测集合一次性运行，覆盖同一批必测项与第八阶段专项测试，结果 `63 passed in 5.22s`。完整 `pytest tests` 已通过，因此本次测试可视为完整运行。

---

## 20. zip 完整性说明

最终交接包文件名：`天工造物_L1_全阶段稳定性整修包_20260603.zip`。

已执行 zip 完整性检查与再解压闭环验证：

```text
test of /mnt/data/天工造物_L1_全阶段稳定性整修包_20260603.zip OK
重新解压后 project/ 文件总数：287
关键文件存在性：通过
```

关键文件存在性检查包括：

- `project/docs/l1_full_stability_repair_report_zh.md`
- `project/tiangong_kernel/l1_ports/candidate_ports.py`
- `project/tests/test_l1_no_duplicate_public_class_names.py`
- `project/tests/test_l1_phase8_candidate_promotion_hint_shape.py`

---

## 21. 是否建议进入二次质检

建议进入二次质检。

理由：P1 已修复，关键 P2 已通过测试或文档收口，但冻结前仍应由质检员复核新增测试、总端口索引、L2-L6 引用矩阵和文件名整理结果。

---

## 22. 是否建议冻结 L1

建议二次质检通过后再冻结。

---

## 23. 修复后工程规模

| 项 | 数量 |
|---|---:|
| 文件总数 | 287 |
| `tiangong_kernel/l1_ports/*.py` | 49 |
| `tests/*.py` | 134 |
| `docs/` 文件 | 41 |

---

## 24. 关键文件 SHA256

```text
51ae4db5d91e797a2dcb02bb3efe2d447e3692679fb7872b6069a6f688170fcb  tiangong_kernel/l1_ports/candidate_ports.py
08bc085d1394818fcbcd264c8731bef3e2c667213f7c455bb4930d4706413e79  tests/test_l1_no_duplicate_public_class_names.py
ef9a8604aa3331d774b46f6f0f413082e4b4dd8f2ce4452f1d838490e0bdb2da  tests/test_l1_phase8_candidate_promotion_hint_shape.py
a88159cfd16d443c8ce3cd7a79c7e868f48e32ef5a59ec9b87e74d6fb032434b  docs/l1_total_port_index_zh.md
f4030093731c5ed2c3a8fc647f2486236e7f64e8a326f34c2e2a0e2dd7105f1c  docs/l1_l2_l6_reference_matrix_zh.md
6d02453ae4585ecdce241f79c1e42238c7610056f5e30ac4105bb307e54a1e0e  docs/l1_legacy_migration_compatibility_notes_zh.md
```
