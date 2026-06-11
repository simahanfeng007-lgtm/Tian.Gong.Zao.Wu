# L6.71.7 / FE01 STEP31Q

## 目标

Provider 设置体验与真实模型接入提示收敛。解决用户不知道为什么仍是 Mock、配置缺什么、保存后是否生效的问题。

## 变更

1. 设置页增加 Provider readiness 摘要：真实模型就绪 / 缺 Provider 配置 / 启动参数锁定 Mock / 配置异常。
2. 首页会话信息与底部模式标签改为明确显示 Mock 缺配置、Mock 锁定或真实模型就绪。
3. Provider 配置检查从“测试连接”改为“检查状态”，明确只读 `/settings/provider`，不裸调 Provider SDK。
4. Provider 保存后继续清空 API Key / Base URL 明文输入框，只展示 configured、digest、错误码、审计号。
5. 新增配置模板按钮，复制不含真实密钥和真实 Base URL 的 JSON 模板。
6. 本地桥接 `/settings/provider` 增加缺失字段、配置文件状态、下一步动作和只读路径 digest 投影。
7. 应用启动时优先读取一次 Runtime 快照，使 Provider 状态在首页首屏可见。
8. 版本统一到 FE01 STEP31Q / L6.71.7。

## 边界

- 前端不调用 Provider SDK。
- 前端不直接执行工具。
- 前端不写长期记忆。
- 前端不写审计。
- 前端不展示、导出、日志打印 API Key / Base URL 明文。
- 本地桥接配置文件不等同于正式 Runtime RC 解阻。

## 验收

新增 `scripts/desktop_provider_settings_acceptance_l6715.py`，验证 Provider readiness、配置模板不含明文、保存后清空明文输入框、Mock 边界不被夸大。
