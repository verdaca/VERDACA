"""TONL error hierarchy."""
from __future__ import annotations


class TONLError(Exception):
    """Base for all TONL errors."""


class TONLParseError(TONLError):
    """Malformed TONL document."""


class TONLValidationError(TONLError):
    """Schema violation or type constraint failure."""


class TONLTypeError(TONLError):
    """Unsupported Python type encountered during encode/decode."""


class TONLSecurityError(TONLError):
    """Security limit violated (nesting, size, etc.)."""
