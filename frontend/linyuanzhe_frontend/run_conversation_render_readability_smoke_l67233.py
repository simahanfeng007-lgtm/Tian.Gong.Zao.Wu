from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



from linyuanzhe_frontend.ui.main_window_chat_runtime import enhance_conversation_readability
from linyuanzhe_frontend.version_info import FE_RUNTIME_VERSION


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    _require((FE_RUNTIME_VERSION.startswith(("L6.72.", "L6.73.")) or FE_RUNTIME_VERSION.startswith("L6.73.")), "frontend version must be L6.72.39")

    dense = (
        "我可以协助完成多种代码任务，包括但不限于： - 软件设计与架构方案 - 前端/后端/UI开发 "
        "- 数据处理与自动化脚本 - 单元测试与集成测试编写 - 代码审查与性能优化 作为计划生成器，我会将你的具体需求转化为可执行步骤。"
    )
    rendered = enhance_conversation_readability(dense, is_assistant=True)
    _require("\n- 软件设计与架构方案" in rendered, "inline hyphen list should become bullet list")
    _require("\n\n作为计划生成器" in rendered, "transition clause should become a new paragraph")

    user_text = "帮我看看桌面有没有垃圾文件 - 不要删除，只分析"
    user_rendered = enhance_conversation_readability(user_text, is_assistant=False)
    _require(user_rendered == user_text, "user content should not be reformatted")

    code = "```python\nprint('hello')\n```"
    code_rendered = enhance_conversation_readability(code, is_assistant=True)
    _require(code_rendered == code, "code fence text should stay unchanged")

    print("PASS L6.72.39 conversation render readability smoke")


if __name__ == "__main__":
    main()
