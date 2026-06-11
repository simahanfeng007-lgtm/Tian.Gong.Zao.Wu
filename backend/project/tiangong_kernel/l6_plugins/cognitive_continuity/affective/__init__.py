"""L6 phase4 affective continuity sub-group.

This sub-group exposes only projection, vector, hint, public projection, and
reentry envelope dataclasses. It cannot decide, permit, write state, write or
remove memory, call models, call tools, or bypass L3/L5.
"""

from __future__ import annotations

from .vectors import *
from .models import *
from .pollution import *
from .style_hints import *
from .memory_modulation import *
from .context_modulation import *
from .governance_binding import *
from .public_projection import *
from .reentry import *
from .invariants import *

__all__ = [name for name in globals() if not name.startswith("_")]
