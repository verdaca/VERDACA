"""Caveman dialect registry."""
from .base import Dialect as DialectProtocol
from .caveman_english import CavemanEnglishDialect
from .wenyan import WenyanDialect

__all__ = ["DialectProtocol", "CavemanEnglishDialect", "WenyanDialect"]
