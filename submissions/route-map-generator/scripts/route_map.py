"""Backward-compatible import path.

Prefer::

    from map_generator import generate
"""

from map_generator import *  # noqa: F403
from map_generator import generate, plan_route

__all__ = ["generate", "plan_route"]
