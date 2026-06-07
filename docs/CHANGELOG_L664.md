# CHANGELOG L6.64

## 新增

- 新增文件传输契约 `tiangong.l6_64.file_transfer_request.v1`。
- 新增 `/files/transfer/request` 契约服务器路径。
- 新增 `/control/task/interrupt` 控制路径。
- 新增桌面端“文件”二级页。
- 首页附件按钮接入文件传输请求链路。
- 首页中断按钮接入 Runtime 控制请求链路。
- 对话引导从静态文本升级为可点击提示词芯片。
- HookBus 增加文件传输请求确定性守卫。
- 新增 L6.64 smoke、preflight、release verifier 和启动脚本。

## 不变

- Runtime 仍是唯一执行调度中枢。
- TiangongWangguan 仍是统一网关入口。
- 前端仍只做渲染、提交请求、展示回执。
- 真实 Runtime 未联调前，RC 状态不标记为 ready。
