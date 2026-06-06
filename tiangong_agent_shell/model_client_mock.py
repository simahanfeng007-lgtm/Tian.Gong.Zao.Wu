"""Mock 模型客户端。"""

from __future__ import annotations

import json
import re

from .config_loader import ModelConfig
from .model_client_port import ChatResult


class MockModelClient:
    provider = "mock"

    def chat(self, messages: list[dict[str, str]], config: ModelConfig) -> ChatResult:
        last_user = ""
        system_text = ""
        for message in messages:
            if message.get("role") == "system":
                system_text += str(message.get("content", "")) + "\n"
        for message in reversed(messages):
            if message.get("role") == "user":
                last_user = message.get("content", "")
                break
        if "计划生成器" in system_text and "steps" in system_text:
            return ChatResult(
                content=json.dumps(_mock_plan(last_user), ensure_ascii=False),
                provider=self.provider,
                model=config.model or "mock-model",
                raw={"mock": True, "planner": True},
            )
        return ChatResult(
            content=f"[MOCK] 已收到：{last_user}",
            provider=self.provider,
            model=config.model or "mock-model",
            raw={"mock": True},
        )


def _extract_task(text: str) -> str:
    match = re.search(r"任务：(.+?)(?:\n|$)", text, flags=re.DOTALL)
    return (match.group(1) if match else text).strip()


def _mock_plan(user_text: str) -> dict:
    """仅供离线 smoke/单测使用的确定性计划输出。真实执行仍由 validator + Runtime 治理链控制。"""
    task = _extract_task(user_text)
    lowered = task.lower()
    steps: list[dict] = []
    if any(word in lowered for word in ["检查", "inspect", "项目", "project"]):
        steps.append({"tool_name": "scan_project", "arguments": {"path": ".", "max_depth": 6, "max_files": 1500}, "reason": "先生成只读项目索引。"})
        steps.append({"tool_name": "list_dir", "arguments": {"path": "."}, "reason": "查看工作区顶层。"})
    if "readme" in lowered or "读取" in lowered or "总结" in lowered:
        steps.append({"tool_name": "read_file", "arguments": {"path": "README.md"}, "reason": "读取 README。"})
    if "写" in lowered or "生成" in lowered or "write" in lowered:
        steps.append(
            {
                "tool_name": "write_workspace_file",
                "arguments": {"path": "model_planner_demo.txt", "content": "L6.14 mock planner generated content."},
                "reason": "生成一个受控工作区文件。",
            }
        )
    if "compileall" in lowered or "测试" in lowered or "test" in lowered or "检查" in lowered or "诊断" in lowered or "修复" in lowered:
        steps.append({"tool_name": "run_python_quality_check", "arguments": {"command": "compileall", "target": "."}, "reason": "运行受控质量检查。"})
    if "诊断" in lowered or "diagnose" in lowered or "修复" in lowered or "repair" in lowered:
        steps.append({"tool_name": "diagnose_project", "arguments": {"path": "."}, "reason": "生成工程诊断摘要。"})
    if "打包" in lowered or "zip" in lowered or "交付" in lowered:
        steps.append({"tool_name": "create_zip_package", "arguments": {"source": ".", "target": "dist/model_planner_demo.zip"}, "reason": "生成交付 zip。"})
    if not steps:
        steps.append({"tool_name": "list_dir", "arguments": {"path": "."}, "reason": "默认安全只读查看。"})
    return {"steps": steps[:8]}
