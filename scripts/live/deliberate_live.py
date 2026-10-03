"""Run one real deliberation from a JSON input and write the receipt.

Usage (repo root, key in the gitignored .env as ANTHROPIC_API_KEY):
    uv run python scripts/live/deliberate_live.py [scripts/live/deliberation_example.json]

Models: VERDACA_PRODUCER_MODEL / VERDACA_REVIEWER_MODEL / VERDACA_SYNTHESIZER_MODEL
(default claude-haiku-4-5). Receipt lands in docs/receipts/.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from praxis.composition.live_deliberation import DEFAULT_MODEL, build_live_deliberator

REPO = Path(__file__).resolve().parents[2]


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "scripts/live/deliberation_example.json"
    data = json.loads(src.read_text())
    deliberate = build_live_deliberator(
        env_path=REPO / ".env",
        receipts_dir=REPO / "docs/receipts",
        producer_model=os.environ.get("VERDACA_PRODUCER_MODEL", DEFAULT_MODEL),
        reviewer_model=os.environ.get("VERDACA_REVIEWER_MODEL", DEFAULT_MODEL),
        synthesizer_model=os.environ.get("VERDACA_SYNTHESIZER_MODEL", DEFAULT_MODEL),
    )
    out = asyncio.run(deliberate(data["question"], data["evidence"]))
    r = out["receipt"]
    print(f"outcome={r['outcome']} reason={r['terminal_reason']} calls={len(r['calls'])} "
          f"cost_usd={r['total_cost_usd']} receipt={out['receipt_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
