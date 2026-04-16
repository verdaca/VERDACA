"""Wenyan (文言文) dialect — classical Chinese compression.

Gated behind accept_wenyan=True (architecture §3.4.2 V-C8).
"""
from __future__ import annotations

_INTENSITY_INSTRUCTIONS: dict[str, str] = {
    "lite": "以文言文大略压缩此文，保留关键信息，词语流畅。",
    "mild": "以文言文适度压缩此文至约七成，去除冗词，保留所有要点。",
    "ultra": "以最简文言文压缩此文至约一成，言简意赅，无一字废，数字与代码原样保留。",
}

_BASE_SYSTEM = """汝为精准文本压缩器。规则：
1. 代码块（```）、行内代码、网址、文件路径、版本号，一律原样保留，不得修改。
2. 不得改变任何陈述之含义或正负性。
3. 不得丢弃数字、日期、专有名词或技术标识符。
4. 保留所有标题（# 号）。
5. 仅输出压缩后文本，不加前言或解释。

压缩要求：{instruction}"""


class WenyanDialect:
    name = "wenyan"

    def system_prompt(self, intensity: str) -> str:
        instruction = _INTENSITY_INSTRUCTIONS.get(intensity, _INTENSITY_INSTRUCTIONS["lite"])
        return _BASE_SYSTEM.format(instruction=instruction)
