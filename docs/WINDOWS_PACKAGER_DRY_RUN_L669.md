# FE01 STEP30 / L6.69 Windows 打包器 dry-run

目标：把合成工程包推进到安装包构建前状态，但仍不输出正式安装器。

## 新增结构

- `installer/build/`：Windows 打包计划、dry-run 脚本、版本槽校验。
- `installer/release/`：发布 manifest 与发布管线预检。
- `installer/signing/`：签名策略占位，不包含证书或私钥。
- `scripts/package_builder_preflight_l669.py`：聚合预检入口。

## 硬边界

1. 不生成 exe/msi。
2. 不保存 Provider 密钥、Runtime 地址明文或签名密钥。
3. 不切换版本槽，不应用更新，不执行回滚。
4. 不修改后端核心主链。
5. 真实 Runtime unlock 未通过时，`ready_for_combine=false` 保持不变。
