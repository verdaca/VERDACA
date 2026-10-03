"""MCP stdio server exposing ``verdaca_deliberate`` for Claude Desktop.

Every tool call is appended to docs/receipts/mcp-server.log (stdout is the MCP
protocol channel, so nothing else may print there). Receipts are written to
docs/receipts/. The Anthropic key is read from the repo's gitignored .env.

Claude Desktop config (claude_desktop_config.json -> mcpServers):
    "verdaca": {
      "command": "uv",
      "args": ["run", "--directory", "<repo>", "python", "scripts/live/deliberate_mcp_server.py"]
    }
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from praxis.adapters.mcp_server.server import create_verdaca_mcp_server
from praxis.composition.live_deliberation import DEFAULT_MODEL, build_live_deliberator

REPO = Path(__file__).resolve().parents[2]


def build_server(env_path: Path = REPO / ".env", receipts_dir: Path = REPO / "docs/receipts") -> FastMCP:
    inner = build_live_deliberator(
        env_path=env_path,
        receipts_dir=receipts_dir,
        producer_model=os.environ.get("VERDACA_PRODUCER_MODEL", DEFAULT_MODEL),
        reviewer_model=os.environ.get("VERDACA_REVIEWER_MODEL", DEFAULT_MODEL),
        synthesizer_model=os.environ.get("VERDACA_SYNTHESIZER_MODEL", DEFAULT_MODEL),
    )
    log = logging.getLogger("verdaca.deliberate")

    async def logged(question: str, evidence: list[dict[str, str]]):
        log.info("verdaca_deliberate called: question=%r evidence_ids=%s",
                 question, [e.get("id") for e in evidence])
        out = await inner(question, evidence)
        r = out["receipt"]
        log.info("verdaca_deliberate done: outcome=%s reason=%s calls=%d cost_usd=%s receipt=%s",
                 r["outcome"], r["terminal_reason"], len(r["calls"]), r["total_cost_usd"],
                 out["receipt_path"])
        return out

    return create_verdaca_mcp_server(deliberator=logged)


def main() -> None:
    (REPO / "docs/receipts").mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=REPO / "docs/receipts/mcp-server.log",
        level=logging.INFO,
        format="%(asctime)sZ %(levelname)s %(message)s",
    )
    build_server().run("stdio")


if __name__ == "__main__":
    main()
