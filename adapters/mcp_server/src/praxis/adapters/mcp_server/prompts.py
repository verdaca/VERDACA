"""Verdaca MCP prompts."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP


def register_prompts(server: FastMCP) -> None:
    """Register prompt templates."""

    @server.prompt(
        name="verdaca-strategy-question",
        title="Ask a Verdaca Decision Question",
        description="Prompt template for framing a Verdaca decision question.",
    )
    def verdaca_strategy_question(question: str, context: str | None = None) -> str:
        lines = [
            f"Decision question: {question}",
            "Use Verdaca to produce a defensible recommendation with cited tradeoffs.",
            "Return the recommendation, cited tradeoffs, dissent frames, and artifacts.",
        ]
        if context:
            lines.insert(1, f"Context: {context}")
        return "\n".join(lines)
