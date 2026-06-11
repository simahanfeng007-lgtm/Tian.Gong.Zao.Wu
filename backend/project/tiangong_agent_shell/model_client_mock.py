"""Mock 模型客户端。仅用于内部 smoke；也遵守 CompiledPromptEnvelope 边界。"""

from __future__ import annotations

import json
import re
from typing import Any

from .config_loader import ModelConfig
from .model_client_port import ChatResult, ensure_compiled_prompt_envelope


class MockModelClient:
    provider = "mock"

    def chat(self, prompt: Any, config: ModelConfig) -> ChatResult:
        envelope = ensure_compiled_prompt_envelope(prompt)
        messages = envelope.as_messages()
        last_user = ""
        system_text = ""
        for message in messages:
            if message.get("role") == "system":
                system_text += str(message.get("content", "")) + "\n"
        for message in reversed(messages):
            if message.get("role") == "user":
                last_user = message.get("content", "")
                break
        if "ActivationFormSpec" in system_text or envelope.phase == "activation_decision":
            return ChatResult(
                content=json.dumps(_mock_activation(system_text, last_user), ensure_ascii=False),
                provider=self.provider,
                model=config.model or "mock-model",
                raw={"mock": True, "activation": True, "prompt": envelope.public_dict()},
            )
        if envelope.phase == "adaptive_repair_plan":
            return ChatResult(
                content=json.dumps(_mock_adaptive_repair_plan(system_text + "\n" + last_user), ensure_ascii=False),
                provider=self.provider,
                model=config.model or "mock-model",
                raw={"mock": True, "adaptive_repair": True, "prompt": envelope.public_dict()},
            )
        if ("PlannerRequest" in system_text and "steps" in system_text) or envelope.phase in {"planner_execution", "planner_plan", "planner"}:
            return ChatResult(
                content=json.dumps(_mock_plan(last_user), ensure_ascii=False),
                provider=self.provider,
                model=config.model or "mock-model",
                raw={"mock": True, "planner": True, "prompt": envelope.public_dict()},
            )
        return ChatResult(
            content=f"[MOCK] 已收到：{last_user}",
            provider=self.provider,
            model=config.model or "mock-model",
            raw={"mock": True, "prompt": envelope.public_dict()},
        )


def _extract_task(text: str) -> str:
    match = re.search(r"任务：(.+?)(?:\n|$)", text, flags=re.DOTALL)
    return (match.group(1) if match else text).strip()


def _mock_activation(system_text: str, user_text: str) -> dict:
    lower = str(user_text or "").lower()
    selected_work = "用户显式模式偏好：work" in system_text or "用户显式模式偏好：工作" in system_text
    work_markers = [
        "创建", "写", "修复", "运行", "执行", "打包", "读取", "列出", "目录",
        "检查", "验证", "诊断", "测试", "质检", "排查", "定位", "模拟", "长链",
        "工作", "项目", "compileall", "pytest", "list", "ls", "write", "fix", "build", "test",
        "inspect", "diagnose", "verify", "run", "execute", "simulate",
    ]
    if not selected_work and not any(x in lower for x in work_markers):
        return {
            "mode": "chat",
            "work_type": "none",
            "execution_depth": "single_turn",
            "tools_requested": False,
            "required_tool_classes": [],
            "risk_level": "A0",
            "need_quality_gate": False,
            "need_user_confirm": False,
            "expected_result": "普通聊天回答",
            "final_output_contract": "answer_only",
        }
    if any(x in lower for x in ["代码", ".py", "pytest", "compile", "compileall", "bug", "runtime", "frontend", "backend", "项目", "诊断", "质检"]):
        work_type = "code"
    elif any(x in lower for x in ["docx", "pdf", "总结文档", "解析文档"]):
        work_type = "document"
    elif any(x in lower for x in ["网页", "搜索", "http", "https"]):
        work_type = "web"
    elif any(x in lower for x in ["文件", ".txt", "目录", "list", "读取", "创建"]):
        work_type = "file"
    else:
        work_type = "mixed"
    depth = "long_chain" if any(x in lower for x in ["完整", "全量", "全部", "打包", "长链", "修复", "继续", "下一步"]) else "multi_step"
    return {
        "mode": "work",
        "work_type": work_type,
        "execution_depth": depth,
        "tools_requested": True,
        "required_tool_classes": ["file_read", "file_write", "terminal_test"] if work_type in {"code", "file", "mixed"} else ["document"],
        "risk_level": "A3",
        "need_quality_gate": True,
        "need_user_confirm": False,
        "expected_result": "真实执行并回传结果",
        "final_output_contract": "execution_report",
    }



def _mock_adaptive_repair_plan(text: str) -> dict:
    lowered = str(text or "").lower()
    if "syntaxerror: expected ':'" in lowered or "expected ':'" in lowered:
        paths = re.findall(r'File "([^"]+\.py)"', text)
        path = paths[-1] if paths else "bad.py"
        before = text.split("SyntaxError: expected ':'", 1)[0]
        candidates: list[str] = []
        for line in before.splitlines():
            raw = line.rstrip("\n")
            if not raw.strip():
                continue
            if raw.lstrip().startswith(("File ", "***", "Listing ", "Compiling ", "^")):
                continue
            if raw.strip().startswith("^"):
                continue
            candidates.append(raw)
        old_line = candidates[-1].strip() if candidates else "def broken()"
        if old_line.endswith(":"):
            new_line = old_line
        else:
            new_line = old_line + ":  # linyuanzhe_l67255_repair"
        try:
            from pathlib import Path as _Path

            path = _Path(path).name if _Path(path).is_absolute() else str(_Path(path))
        except Exception:  # noqa: BLE001
            pass
        return {
            "steps": [
                {
                    "tool_name": "document_apply_rewrite",
                    "arguments": {"path": path, "old_text": old_line, "new_text": new_line, "operation": "replace", "overwrite": True, "allow_no_match": False},
                    "reason": "根据 compileall 缺失冒号错误生成最小修复。",
                },
                {"tool_name": "run_python_quality_check", "arguments": {"command": "compileall", "target": path}, "reason": "复跑 compileall 验证修复。"},
            ]
        }
    if "pytest" in lowered:
        return {
            "steps": [
                {"tool_name": "read_file", "arguments": {"path": "missing_after_pytest_failure.txt"}, "reason": "模拟 repair 失败，验证 partial_with_resume。"}
            ]
        }
    return {
        "steps": [
            {"tool_name": "return_analysis", "arguments": {"content": "未发现可安全自动修复的最小补丁。"}, "reason": "安全返回修复分析。"}
        ]
    }


def _mock_plan(user_text: str) -> dict:
    """仅供离线 smoke/单测使用的确定性计划输出。真实执行仍由 validator + Runtime 治理链控制。"""
    task = _extract_task(user_text)
    lowered = task.lower()
    steps: list[dict] = []
    if any(word in lowered for word in ["检查", "inspect", "项目", "project"]):
        steps.append({"tool_name": "scan_project", "arguments": {"path": ".", "max_depth": 6, "max_files": 1500}, "reason": "先生成只读项目索引。"})
        steps.append({"tool_name": "list_dir", "arguments": {"path": "."}, "reason": "查看工作区顶层。"})
    if "创建" in lowered or "write" in lowered or "写入" in lowered or "生成" in lowered:
        path = "model_planner_demo.txt"
        m = re.search(r"([\w\-.\u4e00-\u9fff]+\.(?:txt|md|json|py|yml|yaml|toml))", task, flags=re.IGNORECASE)
        if m:
            path = m.group(1)
        content = "hello from L6.72.51 activation smoke"
        cm = re.search(r"内容\s*[:：]?\s*(.+)$", task, flags=re.DOTALL)
        if cm:
            raw_content = cm.group(1).strip()
            # Keep content extraction deterministic for chained Chinese prompts:
            # “创建 A.txt 内容：X；修复/测试/打包/总结” should write only X,
            # not swallow the subsequent plan directives into the file body.
            raw_content = re.split(
                r"[；;]\s*(?:然后|并|再|接着)?\s*(?:修复|运行|执行|测试|检查|诊断|打包|输出|总结|汇总|交付)",
                raw_content,
                maxsplit=1,
            )[0].strip()
            content = raw_content[:4000] or content
        steps.append({"tool_name": "write_workspace_file", "arguments": {"path": path, "content": content}, "reason": "按用户要求创建受控工作区文件。"})
    if "readme" in lowered or "读取" in lowered:
        # Prefer existing package README names.  A generic "总结" request should not
        # force a hard-coded README.md read, because many release bundles only ship
        # localized README_*.txt / README_*.md files.
        readme_path = "README.md"
        if "readme" not in lowered and "读取" in lowered:
            readme_path = "README_先看这里_天工造物v2.0-临渊者.txt"
        steps.append({"tool_name": "read_file", "arguments": {"path": readme_path}, "reason": "读取用户显式要求的 README 或文本文件。"})
    if "桌面" in task or "desktop_relative_path=desktop" in lowered or "desktop" in lowered:
        steps.append({"tool_name": "list_dir", "arguments": {"path": "Desktop"}, "reason": "按主机访问提示列出桌面目录。"})
    elif "目录" in lowered or "列出" in lowered or "list" in lowered:
        steps.append({"tool_name": "list_dir", "arguments": {"path": "."}, "reason": "列出工作区目录。"})
    if "compileall" in lowered or "测试" in lowered or "test" in lowered or "检查" in lowered or "诊断" in lowered or "修复" in lowered:
        steps.append({"tool_name": "run_python_quality_check", "arguments": {"command": "compileall", "target": "."}, "reason": "运行受控质量检查。"})
    if "诊断" in lowered or "diagnose" in lowered or "修复" in lowered or "repair" in lowered:
        steps.append({"tool_name": "diagnose_project", "arguments": {"path": "."}, "reason": "生成工程诊断摘要。"})
    if "打包" in lowered or "zip" in lowered or "交付" in lowered:
        steps.append({"tool_name": "create_zip_package", "arguments": {"source": ".", "target": "dist/model_planner_demo.zip"}, "reason": "生成交付 zip。"})
    if any(x in lowered for x in ["总结", "汇总", "报告", "final", "summary", "checkpoint"]):
        steps.append({
            "tool_name": "return_analysis",
            "arguments": {
                "content": "长链模拟收口：已完成计划、执行、观察、验证与总结阶段；具体工具结果以上一阶段输出为准。"
            },
            "reason": "用虚拟分析返回完成长链最终总结，不依赖固定 README.md。",
        })
    if not steps:
        steps.append({"tool_name": "list_dir", "arguments": {"path": "."}, "reason": "默认安全只读查看。"})
    return {"steps": steps[:8]}
