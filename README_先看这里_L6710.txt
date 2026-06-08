临渊者桌面端 FE01 STEP31Q / L6.71.7

本包已按人类使用入口重新归类。根目录不再堆放大量启动脚本。

推荐打开路径：

1. Windows
   打开：01_启动入口/Windows/01_启动临渊者桌面端_自动模式_L6710.bat

2. macOS
   打开：01_启动入口/macOS/01_启动临渊者桌面端_自动模式_L6710.command
   如系统拦截执行权限，在终端运行：chmod +x "01_启动入口/macOS/01_启动临渊者桌面端_自动模式_L6710.command"

3. Linux
   终端运行：bash "01_启动入口/Linux/01_start_desktop_auto_l6710.sh"

入口说明：
- 自动模式：有 Provider Key 时走真实模型；无 Key 时走本地演示桥。
- 真实模型：强制 provider 模式。
- 演示Mock：强制 mock 模式，只做桌面交互验证。
- 一键自检：检查 Python、Tk、项目根目录、桥接入口、配置路径。

旧版 L6705-L6709 根目录入口已移动到：90_历史入口归档/旧版根目录入口_L6705-L6709。
不要再用旧入口做验收。

历史变化（STEP31M/STEP31N）：
- 聊天区增加基础 Markdown 渲染：标题、加粗、列表、引用、分割线、代码块、行内代码、链接识别。
- 聊天消息改为换行保真清洗，保留 Markdown 所需换行；密钥、token、本地路径仍会脱敏。
- 流式 Delta 合并链路保留换行，避免代码块和列表被压成一行。
- 保留上一轮首页对话优先、5 项导航、右侧会话信息折叠、底部极简状态栏。
- 继续维持前端只读边界：不裸调 Provider SDK、不直接调用工具、不写记忆、不绕过 Runtime。

历史变化（STEP31N）：
- 增加发送后的思考态与输出态。
- 保留 Markdown 流式换行，代码块不再因 SSE 清洗压成单行。
- Mock 模式可演示流式 UI，但仍不调用真实模型、工具或记忆系统。

## STEP31Q / L6.71.7 补充

本包继续保持 zip 解压即用，不是 exe/msi 安装器。本轮新增 Provider 状态收敛：若没有真实 AI 回复，请进入“设置 → Provider 配置向导”，填写 Provider、Base URL、API Key、主模型并保存。保存后前端清空明文输入，只显示 configured/digest；真实对话仍通过本地桥接或正式 Runtime 受控链路，不由前端裸调 Provider。

## STEP31Q / L6.71.7 DataUp 补充

本轮新增“DataUp 社区安全更新”入口：
- 桌面端路径：系统 → DataUp 社区安全更新。
- 默认双源：Gitee 主源 + GitHub 备源。
- Gitee：https://gitee.com/yu-yongxiang1994/natures-craftsmanship
- GitHub：https://github.com/simahanfeng007-lgtm/Tian.Gong.Zao.Wu

点击“一键安全更新”后，前端只启动 scripts/dataup_update_core_l6717.py。实际流程为：检查 latest.json → 下载 DataUp zip → 校验 dataup_manifest.json 与 sha256 → 路径白名单/黑名单 → 创建回滚点 → 覆盖允许文件 → 自检 → 失败回滚。

当前 stdlib 更新器实现 manifest sha256 校验与回滚闭环；签名验签槽已预留，不能把未实现的签名验真说成已完成。
