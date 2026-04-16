"""TONLDocument — query and modify a decoded TONL payload without full re-encode."""
from __future__ import annotations

from typing import Any

from .decode import decode
from .encode import encode
from .errors import TONLParseError


class TONLDocument:
    """Mutable wrapper around a TONL-decoded Python object.

    Provides a simple JSONPath-like query and mutation API so downstream agents
    can slice compressed payloads without full decode/re-encode cycles.

    Note: mutation invalidates any cached TONL text; call ``to_text()`` to re-encode.
    """

    def __init__(self, data: Any) -> None:
        self._data = data

    @classmethod
    def parse(cls, text: str) -> "TONLDocument":
        """Parse a TONL-encoded string into a TONLDocument."""
        return cls(decode(text))

    def query(self, path: str) -> list[Any]:
        """Resolve a simple dot-separated path and return all matching values.

        Supports:
        - ``"key"`` — top-level dict key
        - ``"key.subkey"`` — nested key traversal
        - ``"key[*]"`` — list wildcard (returns all elements)
        - ``"key[0]"`` — list index

        Returns a list of matched values (empty list if path not found).
        """
        return list(_resolve(self._data, path.split(".")))

    def insert(self, path: str, value: Any) -> None:
        """Insert or overwrite a value at *path* (dot-separated key traversal only)."""
        keys = path.split(".")
        node = self._data
        for key in keys[:-1]:
            if not isinstance(node, dict) or key not in node:
                raise TONLParseError(f"path {path!r} not found for insert")
            node = node[key]
        if not isinstance(node, dict):
            raise TONLParseError(f"terminal parent at {path!r} is not a dict")
        node[keys[-1]] = value

    def delete(self, path: str) -> None:
        """Delete the value at *path*."""
        keys = path.split(".")
        node = self._data
        for key in keys[:-1]:
            if not isinstance(node, dict) or key not in node:
                raise TONLParseError(f"path {path!r} not found for delete")
            node = node[key]
        if not isinstance(node, dict) or keys[-1] not in node:
            raise TONLParseError(f"key {keys[-1]!r} not found at path {path!r}")
        del node[keys[-1]]

    def to_text(self) -> str:
        """Re-encode the (possibly mutated) document to TONL text."""
        return encode(self._data)

    @property
    def data(self) -> Any:
        return self._data


def _resolve(node: Any, parts: list[str]) -> Any:
    """Generator that yields all values matched by *parts* against *node*."""
    if not parts:
        yield node
        return

    part = parts[0]
    rest = parts[1:]

    # List wildcard
    if part.endswith("[*]"):
        key = part[:-3]
        child = _get(node, key)
        if isinstance(child, list):
            for item in child:
                yield from _resolve(item, rest)
        return

    # List index
    idx_match = part.find("[")
    if idx_match != -1 and part.endswith("]"):
        key = part[:idx_match]
        idx = int(part[idx_match + 1:-1])
        child = _get(node, key)
        if isinstance(child, list) and 0 <= idx < len(child):
            yield from _resolve(child[idx], rest)
        return

    # Plain key
    child = _get(node, part)
    if child is not _MISSING:
        yield from _resolve(child, rest)


_MISSING = object()


def _get(node: Any, key: str) -> Any:
    if isinstance(node, dict):
        return node.get(key, _MISSING)
    return _MISSING
