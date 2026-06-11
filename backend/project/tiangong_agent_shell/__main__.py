"""允许 ``python -m tiangong_agent_shell`` 启动最小智能体外壳。"""

from __future__ import annotations

from .cli_main import main


if __name__ == "__main__":
    raise SystemExit(main())
