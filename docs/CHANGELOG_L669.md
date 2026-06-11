# CHANGELOG L6.69

- 新增 Windows 安装包打包器 dry-run 结构。
- 新增发布 manifest、签名策略占位、版本槽校验。
- 新增聚合预检 `package_builder_preflight_l669.py`。
- 统一启动器新增 `--packager-preflight` 与 `--verify-l669`。
- 仍不输出最终安装包；真实 Runtime 联调未执行时保持阻断。
