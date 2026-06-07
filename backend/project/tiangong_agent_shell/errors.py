"""外壳启动层错误类型。"""

from __future__ import annotations


class AgentShellError(Exception):
    """外壳层可控错误基类。"""

    def __init__(self, user_message: str, *, detail: str | None = None) -> None:
        super().__init__(detail or user_message)
        self.user_message = user_message
        self.detail = detail or user_message


class ConfigError(AgentShellError):
    """配置读取或校验失败。"""


class ModelClientError(AgentShellError):
    """模型调用失败。"""

    def __init__(
        self,
        user_message: str,
        *,
        status_code: int | None = None,
        detail: str | None = None,
    ) -> None:
        super().__init__(user_message, detail=detail)
        self.status_code = status_code
