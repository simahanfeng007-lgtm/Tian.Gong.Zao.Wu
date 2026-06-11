"""TianGong L6 plugin layer package.

L6 starts as public plugin-contract foundation plus inert plugin-group contracts.
Importing this package must not discover plugins, load plugin code, call models,
call tools, mutate lower layers, read credentials, write state, or create a
parallel host.
"""

from __future__ import annotations

__all__ = ("common", "mind", "cognitive_continuity", "governance_control", "product_delivery", "adaptive_collaboration", "final_closure")
