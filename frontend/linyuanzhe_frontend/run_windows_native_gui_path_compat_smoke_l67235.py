from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "frontend"))
sys.path.insert(0, str(ROOT / "backend" / "project"))
sys.path.insert(0, str(ROOT / "desktop"))

from linyuanzhe_frontend.version_info import FE_RUNTIME_VERSION  # noqa: E402
from tiangong_agent_runtime.plan_bridge import PlanBridge  # noqa: E402
from tiangong_agent_runtime.tool_invocation import ToolInvocation  # noqa: E402
from tiangong_agent_runtime.turn_context import TurnContext  # noqa: E402
from tiangong_agent_runtime.adapters.workspace_write_adapter import write_workspace_file_adapter  # noqa: E402
import linyuanzhe_local_runtime_bridge_l671 as bridge  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class EnvPatch:
    def __init__(self, values: dict[str, str]) -> None:
        self.values = values
        self.old: dict[str, str | None] = {}

    def __enter__(self) -> None:
        for key, value in self.values.items():
            self.old[key] = os.environ.get(key)
            os.environ[key] = value

    def __exit__(self, *_exc: object) -> None:
        for key, value in self.old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def main() -> None:
    require((FE_RUNTIME_VERSION.startswith(("L6.72.", "L6.73.")) or FE_RUNTIME_VERSION.startswith("L6.73.")), "frontend version must be L6.72.39")

    with tempfile.TemporaryDirectory(prefix="l67235_win_paths_") as td:
        root = Path(td)
        user = root / "Users" / "tester"
        onedrive = root / "OneDrive"
        (user / "Desktop").mkdir(parents=True)
        (user / "Downloads").mkdir(parents=True)
        (onedrive / "桌面").mkdir(parents=True)
        (onedrive / "文档").mkdir(parents=True)
        with EnvPatch({
            "USERPROFILE": str(user),
            "HOME": str(user),
            "OneDrive": str(onedrive),
            "OneDriveCommercial": str(onedrive),
        }):
            desktop = bridge._known_user_folder("desktop")
            documents = bridge._known_user_folder("documents")
            downloads = bridge._known_user_folder("downloads")
            require(desktop.name == "桌面" and desktop.parent == onedrive, "OneDrive 桌面 should win over local Desktop")
            require(documents.name == "文档" and documents.parent == onedrive, "OneDrive 文档 should resolve")
            require(downloads.name == "Downloads" and downloads.parent == user, "Downloads should fall back to USERPROFILE")

            hint = bridge._host_access_context_hint("system_drive", root)
            require("desktop_relative_path=OneDrive/桌面" in hint, "desktop hint should be relative OneDrive/桌面")
            require("downloads_relative_path=Users/tester/Downloads" in hint, "downloads hint should be relative USERPROFILE/Downloads")
            require("documents_relative_path=OneDrive/文档" in hint, "documents hint should be relative OneDrive/文档")
            require("localized_folder_aliases" in hint, "localized aliases should be advertised")
            require("Windows 管理员目录" in hint, "admin directory warning should be advertised")

            plan = PlanBridge().build_plan("帮我看看桌面有没有垃圾文件\n\n" + hint)
            require(plan and plan[0].tool_name == "list_dir", "桌面检查 should become list_dir")
            require(plan[0].arguments.get("path") == "OneDrive/桌面", "桌面检查 should target OneDrive/桌面")

            plan = PlanBridge().build_plan("读取下载目录里的 report.txt\n\n" + hint)
            require(plan and plan[0].tool_name in {"read_file", "document_parse"}, "下载读取 should become read_file/document_parse")
            require(plan[0].arguments.get("path") == "Users/tester/Downloads/report.txt", "下载读取 should target relative report.txt")

            plan = PlanBridge().build_plan("检查我的文档\n\n" + hint)
            require(plan and plan[0].tool_name == "list_dir", "我的文档检查 should become list_dir")
            require(plan[0].arguments.get("path") == "OneDrive/文档", "我的文档 should target OneDrive/文档")

        kind = bridge._classify_execution_error("PermissionError: [WinError 5] Access is denied; operation requires elevation", 1, "0ms")
        require(kind == "windows_permission_error", "WinError/elevation should classify as windows_permission_error")

        state = bridge.BridgeState(backend_mode="provider", timeout=1)
        state.register_run("run_test", "task_test", "检查桌面", {"frontend_work_mode": "long_chain", "planner_mode": "model_suggest"}, "audit_test")
        require(state.request_reconnect() == 1, "reconnect should mark active run")
        require(state.last_run_state == "reconnecting", "last run state should become reconnecting")
        approval = state.register_bridge_approval(run_id="run_test", audit_id="audit_test", reason="Windows 权限确认", impact_scope="Windows/System32")
        closed = state.submit_bridge_approval(approval["ticket_id"], "approve_once")
        require(closed.get("status") == "approved", "approval submit should close as approved")
        require(closed.get("frontend_decision") == "approve_once", "approval decision should be recorded")

        ctx = TurnContext.create("写入管理员目录", workspace=root)
        result = write_workspace_file_adapter(ToolInvocation("write_workspace_file", {"path": "Windows/System32/demo.txt", "content": "x"}), ctx)
        require(result.status.value == "blocked", "protected Windows write should be blocked")
        require(result.error_code == "windows_permission_required", "protected Windows write should return permission code")

    package_text_files = [
        ROOT / "frontend" / "linyuanzhe_frontend" / "ui" / "main_window_chat_runtime.py",
        ROOT / "frontend" / "linyuanzhe_frontend" / "clients" / "sse_runtime_client.py",
        ROOT / "frontend" / "linyuanzhe_frontend" / "clients" / "mock_runtime_client.py",
    ]
    for path in package_text_files:
        require("临渊者" + "正在思考" not in path.read_text(encoding="utf-8"), f"thinking label should be shortened in {path.name}")
        require("正在思考" in path.read_text(encoding="utf-8"), f"short thinking label should exist in {path.name}")

    print("PASS L6.72.39 Windows native GUI/path compatibility smoke")


if __name__ == "__main__":
    main()
