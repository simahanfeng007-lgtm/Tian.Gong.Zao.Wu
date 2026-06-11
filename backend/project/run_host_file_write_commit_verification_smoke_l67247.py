from __future__ import annotations

import os
import tempfile
from pathlib import Path

from tiangong_agent_runtime.adapters.document_context_adapters import document_export_adapter
from tiangong_agent_runtime.adapters.document_parse_adapter import document_parse_adapter
from tiangong_agent_runtime.adapters.readonly_file_adapter import list_dir_adapter, read_file_adapter
from tiangong_agent_runtime.adapters.workspace_write_adapter import write_workspace_file_adapter
from tiangong_agent_runtime.document_context_store import save_document_context
from tiangong_agent_runtime.document_parser import parse_document
from tiangong_agent_runtime.host_path_normalizer import normalize_host_known_folder_path
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.tool_result import ToolResultStatus
from tiangong_agent_runtime.turn_context import TurnContext


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        real_desktop = root / "OneDrive" / "桌面"
        real_downloads = root / "Users" / "tester" / "Downloads"
        real_documents = root / "OneDrive" / "文档"
        real_desktop.mkdir(parents=True)
        real_downloads.mkdir(parents=True)
        real_documents.mkdir(parents=True)

        os.environ["LINYUANZHE_DESKTOP_RELATIVE_PATH"] = "OneDrive/桌面"
        os.environ["LINYUANZHE_DOWNLOADS_RELATIVE_PATH"] = "Users/tester/Downloads"
        os.environ["LINYUANZHE_DOCUMENTS_RELATIVE_PATH"] = "OneDrive/文档"

        host_hint = "\n\n[桌面端主机文件访问提示]\n- desktop_relative_path=OneDrive/桌面\n- downloads_relative_path=Users/tester/Downloads\n- documents_relative_path=OneDrive/文档\n"
        ctx = TurnContext.create("在桌面创建文件" + host_hint, workspace=root)
        synthetic_path = "Users/User/Desktop/天宫造物/成都新能源货车租赁·抖音运营执行方案（优化版）.txt"
        normalized = normalize_host_known_folder_path(synthetic_path, ctx.user_message)
        require(normalized.changed, "Users/User/Desktop must normalize to real desktop")
        require(normalized.normalized_path.startswith("OneDrive/桌面/"), "normalized path must use desktop hint")

        write_result = write_workspace_file_adapter(
            ToolInvocation("write_workspace_file", {"path": synthetic_path, "content": "执行方案正文\n第一条：测试真实落盘。"}),
            ctx,
        )
        require(write_result.status is ToolResultStatus.OK, f"write failed: {write_result.output_summary}")
        require(bool(write_result.data.get("physical_commit_verified")), "write must be physically verified")
        expected_file = real_desktop / "天宫造物" / "成都新能源货车租赁·抖音运营执行方案（优化版）.txt"
        wrong_file = root / "Users" / "User" / "Desktop" / "天宫造物" / "成都新能源货车租赁·抖音运营执行方案（优化版）.txt"
        require(expected_file.exists(), "file must land in real known desktop path")
        require(not wrong_file.exists(), "synthetic Users/User/Desktop path must not be created")
        require("测试真实落盘" in expected_file.read_text(encoding="utf-8"), "read-after-write content mismatch")

        read_result = read_file_adapter(ToolInvocation("read_file", {"path": synthetic_path}), ctx)
        require(read_result.status is ToolResultStatus.OK, f"read synthetic path failed: {read_result.output_summary}")
        require("测试真实落盘" in read_result.output_summary, "read_file must resolve same synthetic path")
        list_result = list_dir_adapter(ToolInvocation("list_dir", {"path": "Users/User/Desktop/天宫造物"}), ctx)
        require(list_result.status is ToolResultStatus.OK, f"list synthetic desktop folder failed: {list_result.output_summary}")
        require("成都新能源" in list_result.output_summary, "list_dir must show physically written file")

        parse_result = document_parse_adapter(ToolInvocation("document_parse", {"path": synthetic_path}), ctx)
        require(parse_result.status is ToolResultStatus.OK, f"document_parse synthetic path failed: {parse_result.output_summary}")

        parsed = parse_document(expected_file)
        doc_ctx, _ = save_document_context(root, parsed)
        export_result = document_export_adapter(
            ToolInvocation("document_export", {"document_id": doc_ctx["document_id"], "target": "Users/User/Desktop/天宫造物/导出摘要.md", "format": "md"}),
            ctx,
        )
        require(export_result.status is ToolResultStatus.OK, f"document_export failed: {export_result.output_summary}")
        require(bool(export_result.data.get("physical_commit_verified")), "document_export must be physically verified")
        require((real_desktop / "天宫造物" / "导出摘要.md").exists(), "document_export must land in real desktop path")

    print("PASS L6.72.47 host file write commit verification smoke")


if __name__ == "__main__":
    main()
