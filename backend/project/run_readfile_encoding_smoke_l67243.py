from __future__ import annotations

import tempfile
from pathlib import Path

from tiangong_agent_runtime.adapters.readonly_file_adapter import read_file_adapter
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.turn_context import TurnContext


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        gb = root / "中文-gb18030.txt"
        gb.write_bytes("新能源货车租赁文案".encode("gb18030"))
        ctx = TurnContext.create("read", workspace=root)
        result = read_file_adapter(ToolInvocation("read_file", {"path": "中文-gb18030.txt"}), ctx)
        require(result.status.value == "ok", "gb18030 read should succeed")
        require("新能源货车租赁文案" in result.output_summary, "gb18030 text should decode without mojibake")
        require("�" not in result.output_summary, "decoded text must not contain replacement chars")

        binary = root / "sample.docx"
        binary.write_bytes(b"PK\x03\x04\x00\x00\x00\x00binary-docx-payload")
        result2 = read_file_adapter(ToolInvocation("read_file", {"path": "sample.docx"}), ctx)
        require(result2.status.value == "ok", "binary metadata read should be ok")
        require("疑似二进制" in result2.output_summary, "binary content should be summarized, not dumped")
        require("PK" not in result2.output_summary, "raw binary signature should not leak")

    print("PASS L6.72.43 read_file adapter encoding smoke")


if __name__ == "__main__":
    main()
