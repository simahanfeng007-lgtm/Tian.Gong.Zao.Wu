# L6 第一阶段 forbidden scan 结果

生成日期：2026-06-05

## 结论

- L6 common AST 禁止导入扫描：True
- 默认 forbidden rule 数量：20
- clean sample passed：True
- dirty sample passed：False
- dirty sample P0 命中数：5

说明：`forbidden_scan.py` 本身需要保存 forbidden pattern 字符串作为规则数据，因此自身源码不做简单 raw substring 扫描；对 L6 common 源码采用 AST import 边界扫描，对未来插件源码采用 `scan_l6_text`。

证据文件：`docs/forbidden_scan_l6_phase1_20260605.json`
