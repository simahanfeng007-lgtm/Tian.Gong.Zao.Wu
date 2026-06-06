# L0 第 2 阶段开发日志：事实轨迹

- 日期：2026-06-03
- 范围：event.py、observation.py、signal.py、metric.py、content.py、message.py
- 层级：L0 零依赖原语层

## 目标

建立事件、观察、信号、指标、内容引用与消息事实对象，为上层系统提供统一事实表达。

## 已完成模块与对象

- `event.py`：事件引用、事件类型、事件状态、事件元数据与载荷引用。
- `observation.py`：观察引用、来源、质量、窗口与载荷引用。
- `signal.py`：信号引用、种类、强度、极性、置信度与窗口。
- `metric.py`：指标引用、单位、值、窗口、聚合与序列引用。
- `content.py`：内容、载荷、摘要、媒体类型、编码、安全与处置引用。
- `message.py`：消息引用、角色、状态与核心消息事实。

## 设计取舍

- 只表达事实引用，不保存大内容体。
- 事件层不实现 EventStore、EventBus、dispatch 或 replay。
- 消息层不构造 prompt、不调用模型、不拼接上下文。

## 本轮修复记录

- 为阶段 2 模块补中文边界说明。
- 为阶段 2 核心类补中文 docstring。

## 测试命令与结果

- `python -m pytest tests/test_l0_phase2* -q`：3 passed。

## 未做事项

- 未实现采集器、RAG、prompt builder、模型客户端、文件或网络访问。
