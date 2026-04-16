"""Caveman English dialect — terse, compressed prose in primitive English."""
from __future__ import annotations

_INTENSITY_INSTRUCTIONS: dict[str, str] = {
    "lite": (
        "Compress this text minimally. Remove filler words, redundant phrases, and "
        "unnecessary padding. Keep all key information. Output must be grammatically valid."
    ),
    "mild": (
        "Compress this text to ~70% of original length. Remove filler, combine sentences "
        "where natural, but keep all key facts, numbers, and instructions intact."
    ),
    "moderate": (
        "Compress this text to ~50% of original length. Use short punchy sentences. "
        "Remove all hedging and repetition. Preserve all facts, numbers, code, and URLs exactly."
    ),
    "heavy": (
        "Compress aggressively to ~35% of original. Use noun phrases, drop articles/conjunctions "
        "where meaning is clear. Every word must earn its place. No information loss."
    ),
    "extreme": (
        "Compress to ~20% of original using telegram-style terse notation. Abbreviate freely. "
        "All facts, numbers, and critical information must survive. No code blocks touched."
    ),
    "ultra": (
        "Maximum compression: ~10% of original. Use the most minimal representation possible "
        "while retaining EVERY fact, number, decision, and constraint. No paraphrasing of "
        "technical content. Code blocks are sacred — never modify them."
    ),
}

_BASE_SYSTEM = """You are a precision text compressor. Your rules:
1. NEVER modify content inside ``` code blocks, inline `code`, URLs, file paths, or version numbers.
2. NEVER change the sign or meaning of any statement (do not flip "not allowed" to "allowed").
3. NEVER drop numbers, dates, proper nouns, or technical identifiers.
4. Preserve all headings (# marks).
5. Output ONLY the compressed text — no preamble, no explanation.

Compression instruction: {instruction}"""


class CavemanEnglishDialect:
    name = "caveman_english"

    def system_prompt(self, intensity: str) -> str:
        instruction = _INTENSITY_INSTRUCTIONS.get(intensity, _INTENSITY_INSTRUCTIONS["moderate"])
        return _BASE_SYSTEM.format(instruction=instruction)
