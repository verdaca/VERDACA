"""Load pricing snapshots from JSON. Rates must be string-encoded to avoid float parsing."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from ..models import CacheRetention, Currency, ModelPricing, ProviderName

RATE_FIELDS = ("input_rate", "output_rate", "cache_read_rate", "cache_write_rate")


def _parse_iso_utc(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def _coerce_rate(name: str, raw: Any) -> Decimal:
    if isinstance(raw, float):
        raise ValueError(
            f"{name} must be string-encoded in snapshot JSON (got float {raw!r})"
        )
    if isinstance(raw, int):
        return Decimal(raw)
    if isinstance(raw, str):
        return Decimal(raw)
    raise ValueError(f"{name} has unsupported type {type(raw).__name__}")


def load_snapshot_file(path: Path) -> tuple[list[ModelPricing], str]:
    """Parse a single snapshot JSON file. Returns (rows, sha256_hex)."""
    raw_bytes = path.read_bytes()
    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    data = json.loads(raw_bytes.decode("utf-8"))

    if not isinstance(data, dict) or "rows" not in data:
        raise ValueError(f"snapshot {path.name} missing 'rows' key")

    out: list[ModelPricing] = []
    for idx, row in enumerate(data["rows"]):
        try:
            out.append(
                ModelPricing(
                    provider=ProviderName(row["provider"]),
                    model_id=row["model_id"],
                    cache_retention_key=CacheRetention(
                        row.get("cache_retention_key", "none")
                    ),
                    currency=Currency(row.get("currency", "USD")),
                    input_rate=_coerce_rate("input_rate", row["input_rate"]),
                    output_rate=_coerce_rate("output_rate", row["output_rate"]),
                    cache_read_rate=_coerce_rate(
                        "cache_read_rate", row["cache_read_rate"]
                    ),
                    cache_write_rate=_coerce_rate(
                        "cache_write_rate", row["cache_write_rate"]
                    ),
                    effective_from=_parse_iso_utc(row["effective_from"]),
                    effective_until=(
                        _parse_iso_utc(row["effective_until"])
                        if row.get("effective_until")
                        else None
                    ),
                    source_url=row.get("source_url"),
                    snapshot_sha256=sha256,
                )
            )
        except (KeyError, ValueError) as exc:
            raise ValueError(f"{path.name} row {idx}: {exc}") from exc

    return out, sha256


def load_snapshot_dir(directory: Path) -> list[ModelPricing]:
    """Load every *.json snapshot in a directory (non-recursive)."""
    rows: list[ModelPricing] = []
    for path in sorted(directory.glob("*.json")):
        file_rows, _ = load_snapshot_file(path)
        rows.extend(file_rows)
    return rows
