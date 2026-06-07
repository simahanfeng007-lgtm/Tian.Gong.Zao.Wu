"""CLI 主入口。"""

from __future__ import annotations

import argparse
import sys

from .cli_loop import format_config, format_status, run_interactive, run_once, write_line
from .composition_root import build_agent_context
from .config_loader import load_model_config
from .errors import AgentShellError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_agent.py",
        description="天工造物 v2 外壳式智能体启动器 / 临渊者执行链冻结 Runtime",
    )
    parser.add_argument("--mock", action="store_true", help="使用 Mock 模型，不需要 API Key。")
    parser.add_argument("--once", metavar="TEXT", help="单轮输入并退出。")
    parser.add_argument("--config", help="模型配置 JSON 文件路径。")
    parser.add_argument("--provider", help="模型 Provider，例如 openai_compatible。")
    parser.add_argument("--base-url", dest="base_url", help="OpenAI-compatible Base URL。")
    parser.add_argument("--api-key", dest="api_key", help="API Key。建议优先使用环境变量。")
    parser.add_argument("--model", help="模型名。")
    parser.add_argument("--timeout", type=float, help="请求超时时间，单位秒。")
    parser.add_argument(
        "--tool-mode",
        dest="tool_mode",
        choices=["disabled", "dry_run", "runtime_governed"],
        help="工具桥模式；默认 disabled。runtime_governed 将启用 L6.32 Planner 执行主链。",
    )
    parser.add_argument("--workspace", help="L6.10 受治理工具工作区；默认当前目录。")
    parser.add_argument(
        "--planner-mode",
        dest="planner_mode",
        choices=["rule_only", "model_suggest", "model_required"],
        help="L6.14 自然语言计划生成模式；默认 rule_only。",
    )
    parser.add_argument("--max-steps", type=int, default=20, help="单轮最多执行步骤数；默认 20。")
    parser.add_argument("--status", action="store_true", help="显示状态后退出。")
    parser.add_argument("--show-config", action="store_true", help="显示脱敏配置后退出。")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = load_model_config(args)
        context = build_agent_context(config, workspace=args.workspace, max_steps=args.max_steps)
        if args.status:
            write_line(format_status(context))
            return 0
        if args.show_config:
            write_line(format_config(context))
            return 0
        if args.once is not None:
            return run_once(context, args.once)
        return run_interactive(context)
    except AgentShellError as exc:
        write_line(f"[错误] {exc.user_message}", stream=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - keep CLI user-facing and non-crashy
        write_line(f"[错误] 启动器遇到未预期错误：{exc.__class__.__name__}。", stream=sys.stderr)
        write_line("可使用 --mock 验证启动链，或检查配置文件与环境变量。", stream=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
