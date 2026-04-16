"""Forge compaction error hierarchy."""
from __future__ import annotations


class ForgeError(Exception):
    """Base for all Forge errors."""


class CompactionError(ForgeError):
    """Compaction algorithm failure."""


class ReasoningExtractionError(ForgeError):
    """Reasoning block extraction or injection failed."""


class TemplateRenderError(ForgeError):
    """Jinja2 template rendering failed — this is a build bug."""
