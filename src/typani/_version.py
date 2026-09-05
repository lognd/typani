"""Single source of truth for typani's version string (T-0010).

Split out of __init__.py so scripts/bump_version.py rewrites one literal
here instead of __init__.py's import block, and so typani._impl can read
the version without importing typani's full public surface (avoiding a
circular import between typani/__init__.py and typani/_impl.py).
"""

from __future__ import annotations

__version__ = "0.1.0"
