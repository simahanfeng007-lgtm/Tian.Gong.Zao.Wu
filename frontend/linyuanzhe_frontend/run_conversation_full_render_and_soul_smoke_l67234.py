from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



import re

from linyuanzhe_frontend.contracts.provider_settings import ProviderSettingsWriteRequest, SOUL_PROMPT_CHAR_LIMIT
from linyuanzhe_frontend.ui.main_window import LinyuanzheDesktopApp
from linyuanzhe_frontend.ui.main_window_chat_runtime import ChatRuntimeMixin, enhance_conversation_readability
from linyuanzhe_frontend.version_info import FE_RUNTIME_VERSION, PROVIDER_CONFIG_SCHEMA_VERSION


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class FakeText:
    def __init__(self) -> None:
        self.parts: list[tuple[str, tuple[str, ...]]] = []

    def insert(self, _where: str, text: str, tags=()) -> None:
        if isinstance(tags, str):
            tags = (tags,)
        self.parts.append((text, tuple(tags)))

    @property
    def text(self) -> str:
        return "".join(part for part, _tags in self.parts)

    @property
    def tags(self) -> set[str]:
        out: set[str] = set()
        for _part, tags in self.parts:
            out.update(tags)
        return out


class RenderHarness(ChatRuntimeMixin):
    _INLINE_MD_RE = LinyuanzheDesktopApp._INLINE_MD_RE


def main() -> None:
    require((FE_RUNTIME_VERSION.startswith(("L6.72.", "L6.73.")) or FE_RUNTIME_VERSION.startswith("L6.73.")), "frontend version must be L6.72.39")
    require(PROVIDER_CONFIG_SCHEMA_VERSION.startswith("tiangong.l6_73_") or PROVIDER_CONFIG_SCHEMA_VERSION.endswith(("l6_72_52.local_provider_config.v1", "l6_73_5.local_provider_config.v1")), "provider schema must accept L6.72.52+ / L6.73.x")
    require(SOUL_PROMPT_CHAR_LIMIT >= 6000, "soul prompt limit must be expanded")

    long_soul = "第一段：临渊者是 LLM 的身体化执行外骨骼。\n\n" + ("执行力第一，但不自治夺权。" * 360)
    req = ProviderSettingsWriteRequest.from_form({
        "provider": "deepseek",
        "model": "deepseek-v4-pro",
        "persona_name": "临渊者",
        "persona_prompt": long_soul,
    })
    require("\n\n" in req.persona_prompt, "soul prompt should preserve paragraphs")
    require(len(req.persona_prompt) > 3000, "soul prompt should not be clipped to old 500/1200 limits")

    dense = "return_analysis: hidden\n我可以处理： - 规划 - 代码 - 文件 - 测试 作为任务工作台，我会分步骤回传。"
    readable = enhance_conversation_readability(dense, is_assistant=True)
    require("return_analysis" not in readable, "internal render signal must be stripped")
    require("\n- 规划" in readable, "dense inline bullets must be split")

    md = """# 标题

| 项 | 状态 |
| --- | --- |
| Soul | 扩容 |
| 渲染 | 完成 |

- [ ] 待办
- [x] 完成

工具：list_dir 已启动
成功：smoke 通过
警告：需要本机 GUI 复验
错误：示例错误

> 引用内容

[1]: 来源说明

```python
print('ok')
```
"""
    fake = FakeText()
    RenderHarness()._insert_markdown_text(fake, md, ("body", "bubble_assistant"))
    rendered = fake.text
    tags = fake.tags
    require("Soul" in rendered and "md_table" in tags and "md_table_header" in tags, "markdown table should render")
    require("☐" in rendered and "☑" in rendered and "md_task_pending" in tags and "md_task_done" in tags, "task list should render")
    require("▣" in rendered and "✓" in rendered and "⚠" in rendered and "✖" in rendered, "event/status lines should render")
    require("↳" in rendered and "md_citation" in tags, "citation/footnote lines should render")
    require("python" in rendered and "md_code_block" in tags, "code fence should render")

    print("PASS L6.72.39 conversation full render and soul smoke")


if __name__ == "__main__":
    main()
