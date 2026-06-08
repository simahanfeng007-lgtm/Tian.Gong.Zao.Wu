DataUp 社区更新目录说明 / L6.71.7

用途：
- 为临渊者桌面端提供开源社区安全更新包索引与包格式。
- 当前包内提供更新器壳、manifest 校验器、回滚器和索引模板。

默认双源：
- Gitee 主源：https://gitee.com/yu-yongxiang1994/natures-craftsmanship
- GitHub 备源：https://github.com/simahanfeng007-lgtm/Tian.Gong.Zao.Wu

仓库建议结构：
dataup/
  latest.json
  index.json
  packages/
    <DataUp更新包>.zip
  public_keys/
    tiangong_dataup_public_key.pem

边界：
- DataUp 更新器不得覆盖 Provider 配置、API Key、.env、记忆、日志、审计私密数据、credentials、用户工作区。
- 更新前必须创建 backups/dataup_rollback_YYYYMMDD_HHMMSS。
- 更新后必须执行 compileall、secret scan、desktop bundle preflight；失败自动回滚。
- 当前 stdlib 更新器实现 manifest sha256 校验；签名验签槽预留，不能把签名预留说成已验签。
