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
    """模型调用失败。

    L6.72.58 起附带 ProviderError 归一分类字段。旧调用只传
    user_message/status_code/detail 仍然兼容；新 adapter 会填入
    error_kind/provider/retryable，供 Runtime/Planner 主动策略判断。
    """

    def __init__(
        self,
        user_message: str,
        *,
        status_code: int | None = None,
        detail: str | None = None,
        error_kind: str = "",
        provider: str = "",
        retryable: bool = False,
    ) -> None:
        super().__init__(user_message, detail=detail)
        self.status_code = status_code
        self.error_kind = str(error_kind or "")
        self.provider = str(provider or "")
        self.retryable = bool(retryable)
