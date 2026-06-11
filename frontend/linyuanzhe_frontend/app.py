from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from linyuanzhe_frontend.clients import FutureRuntimeClient, JsonReportRuntimeClient, SseRuntimeClient
from linyuanzhe_frontend.version_info import FE_FULL_VERSION


def build_client(args: argparse.Namespace):
    runtime_url = args.runtime_url or os.environ.get("LINYUANZHE_RUNTIME_URL")
    if runtime_url:
        return SseRuntimeClient(runtime_url, timeout=args.runtime_timeout)
    if args.json_report:
        return JsonReportRuntimeClient(args.json_report)
    if args.future_placeholder:
        return FutureRuntimeClient(args.future_placeholder)
    raise SystemExit("未检测到本地运行时桥接地址。请从 START_FROM_ANYWHERE_AUTO_L6729.bat 启动；或先在设置页填写服务地址与接口密钥后由本地桥接接管。")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"临渊者桌面端 {FE_FULL_VERSION}")
    parser.add_argument("--json-report", default=None, help="读取后端导出的 JSON 报告文件或目录，只读")
    parser.add_argument("--future-placeholder", default=None, help="FutureRuntimeClient 占位端点，保留兼容")
    parser.add_argument("--runtime-url", default=None, help="本地运行时桥接地址，只连接流式事件/控制请求/联调契约端点")
    parser.add_argument("--runtime-timeout", type=float, default=float(os.environ.get("LINYUANZHE_FRONTEND_RUNTIME_TIMEOUT", "900") or 900), help="运行时 HTTP/流式事件空闲超时秒数；长任务默认 900 秒")
    args = parser.parse_args(argv)
    client = build_client(args)

    from linyuanzhe_frontend.ui.main_window import LinyuanzheDesktopApp

    app = LinyuanzheDesktopApp(client)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
