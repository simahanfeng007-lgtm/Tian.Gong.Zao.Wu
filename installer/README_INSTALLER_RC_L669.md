# L6.69 Windows 安装包打包器 dry-run / 发布管线预检

本目录是在 L6.68 安装器 RC 前置结构之上新增的打包器前置层。它只生成构建计划、版本槽校验、发布 manifest 校验和 dry-run 报告。

边界：

- 不生成最终 exe/msi。
- 不读取、不保存、不打包签名证书或私钥。
- 不自动应用更新。
- 不切换版本槽。
- 不修改 Runtime 核心主链。
- 真实 Runtime smoke 未通过前，不得标记正式 RC。

推荐入口：

```bash
python installer/startup/startup_self_check_l669.py
python installer/build/package_builder_dry_run_l669.py
python installer/build/version_slot_validate_l669.py
python installer/release/release_pipeline_preflight_l669.py
python scripts/package_builder_preflight_l669.py
```
