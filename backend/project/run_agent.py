"""天工造物 L6.9 外壳式最小智能体启动入口。

该入口只装配外壳层 ``tiangong_agent_shell``，不把 CLI/API/session
逻辑写入 ``tiangong_kernel`` 主体，从而保持 L6 冻结内核不被污染。
"""

from __future__ import annotations

from tiangong_agent_shell.cli_main import main


if __name__ == "__main__":
    raise SystemExit(main())
