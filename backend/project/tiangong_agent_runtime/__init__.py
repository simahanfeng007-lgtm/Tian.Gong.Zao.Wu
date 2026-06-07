"""天工造物 L6.51.1 受治理真实运行链。

本包是外壳层与 L6 主体内核之间的运行脊柱：
- 可以依赖 tiangong_kernel 的对象/契约；
- tiangong_kernel 不应反向依赖本包；
- 工具执行必须经风险分级、permit、registry、adapter 与 audit。
"""

from __future__ import annotations

from .product_identity import build_product_identity_public

__all__ = ["__version__", "build_product_identity_public"]

__version__ = "0.1.0-l6.51.1"
