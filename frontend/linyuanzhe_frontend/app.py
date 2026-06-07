from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from linyuanzhe_frontend.clients import FutureRuntimeClient, JsonReportRuntimeClient, MockRuntimeClient, SseRuntimeClient
from linyuanzhe_frontend.ui.main_window import LinyuanzheDesktopApp


def build_client(args: argparse.Namespace):
    runtime_url = args.runtime_url or os.environ.get("LINYUANZHE_RUNTIME_URL")
    if runtime_url:
        return SseRuntimeClient(runtime_url, timeout=args.runtime_timeout)
    if args.json_report:
        return JsonReportRuntimeClient(args.json_report)
    if args.future_placeholder:
        return FutureRuntimeClient(args.future_placeholder)
    return MockRuntimeClient(args.mock_file)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="临渊者桌面驾驶舱 FE01 STEP23 / L6.62")
    parser.add_argument("--mock-file", default=None, help="读取前端 Mock RuntimeSnapshot JSON")
    parser.add_argument("--json-report", default=None, help="读取后端导出的 JSON 报告文件或目录，只读")
    parser.add_argument("--future-placeholder", default=None, help="FutureRuntimeClient 占位端点，保留兼容")
    parser.add_argument("--runtime-url", default=None, help="L6.62 正式 Runtime 网关地址，只连接 Runtime SSE/控制请求/联调契约端点")
    parser.add_argument("--runtime-timeout", type=float, default=30.0, help="Runtime HTTP/SSE 超时秒数")
    args = parser.parse_args(argv)
    client = build_client(args)
    app = LinyuanzheDesktopApp(client)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
