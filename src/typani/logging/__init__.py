"""typani's central logging channel -- every module logs through get_logger."""

from __future__ import annotations

from typani.logging.logger import configure, get_logger

__all__ = ["configure", "get_logger"]
