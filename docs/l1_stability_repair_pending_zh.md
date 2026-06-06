# L1 全阶段稳定性整修待办（修复后版）

生成时间：2026-06-03

## 1. 已处理项

- 已修复：`candidate_ports.py` 内 `CandidatePromotionHint` 重复定义覆盖问题。
- 已补测试：`tests/test_l1_no_duplicate_public_class_names.py`，禁止同一 L1 模块重复公开顶层类名。
- 已补测试：`tests/test_l1_phase8_candidate_promotion_hint_shape.py`，确认统一候选晋升提示保留学习、迭代、进化三类候选字段。
- 已补文档：`docs/l1_total_port_index_zh.md`，说明总端口索引、动词口径、候选/验证/变更/实验层级、L0 Ref 策略和旧体系边界。
- 已补文档：`docs/l1_l2_l6_reference_matrix_zh.md`，说明 L1 到 L2-L6 的引用矩阵和反向依赖禁令。
- 已补文档：`docs/l1_legacy_migration_compatibility_notes_zh.md`，说明新版不恢复旧能力包体系。
- 已整理乱码文件名：`design/` 下两份设计文档已改为正常中文文件名；根目录两份 L0 交付报告已移入 `docs/` 并改为正常文件名。

## 2. 保留设计口径

- `validation_ports.py` 与 `candidate_ports.py` 跨模块保留 `CandidatePromotionHint*` 同名对象。前者偏验证链输出提示，后者偏统一候选生命周期提示；通过总端口索引说明边界，不做大面积重命名。
- `tiangong_kernel/l1_ports/__init__.py` 保持稳定骨架导出策略。第 2-8 阶段端口通过子模块显式导入，不平铺导出 200+ 对象。
- 候选引用继续使用 L0 `ResourceRef`。当前 L0 没有专用 `CandidateRef`，本次不新增 L0 原语。
- `RuntimeContextPort` 与 `RuntimeStateRef` 仅表示运行上下文和运行状态引用，不是旧 Runtime 主循环。

## 3. 仍建议二次质检关注项

1. 复核新增测试是否足以覆盖重复类名与候选晋升字段形状。
2. 复核总端口索引是否满足 L2-L6 后续引用需要。
3. 复核乱码文件名整理是否符合归档预期。
4. 用户如提供独立 L0 最终归档包，建议做跨包 hash 比对；本次未收到独立 L0 基线，因此只能保证本轮修复未改动 `tiangong_kernel/l0_primitives/`。

## 4. 不在本次修复中处理的事项

- 不统一全项目所有端口方法名，避免破坏已有协议面。
- 不新增 L0 `CandidateRef`，避免修改 L0。
- 不重命名跨模块 `CandidatePromotionHint*`，避免扩大兼容面。
- 不抽取测试扫描 helper，避免无必要重构测试体系。
- 不进入 L2-L6 设计或实现。
