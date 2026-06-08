# STEP31Q / L6.71.7 DataUp 一键安全更新入口

## 本轮新增

- 系统页新增 DataUp 社区安全更新卡片。
- 内置 Gitee 主源与 GitHub 备源。
- 新增独立更新器：`scripts/dataup_update_core_l6717.py`。
- 新增 manifest 校验器：`scripts/dataup_manifest_validate_l6717.py`。
- 新增回滚器：`scripts/dataup_rollback_l6717.py`。
- 新增桌面 helper：`desktop/dataup_update_helper_l6717.py`。
- 新增三端入口：Windows / macOS / Linux / 通用 Python。
- 新增 DataUp 包格式模板与 latest.json 示例。

## 安全边界

- 前端不直接复制或覆盖文件。
- 默认阻断 Provider 配置、API Key、.env、记忆、日志、审计私密数据、credentials、用户工作区。
- 默认阻断 backend/runtime 核心路径。
- 更新前创建 `backups/dataup_rollback_YYYYMMDD_HHMMSS`。
- 更新后运行 compileall、secret scan、desktop bundle preflight；失败自动回滚。
- 当前实现 manifest sha256 校验，签名验签槽预留。

## 验证

- `python -m compileall -q frontend desktop scripts`
- `python scripts/desktop_dataup_update_acceptance_l6717.py`
- `python scripts/desktop_bundle_preflight_l671.py`
- `python scripts/verify_l671_release.py`
- `python scripts/scan_l659.py`
