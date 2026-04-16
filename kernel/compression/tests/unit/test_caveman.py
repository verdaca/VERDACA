"""Unit tests — Caveman gate, validators, boundary detection."""
from __future__ import annotations

import pytest

from praxis.kernel.compression.caveman.boundary import (
    classify_content,
    extract_code_blocks,
    extract_paths,
    extract_urls,
)
from praxis.kernel.compression.caveman.gate import (
    CalibrationSnapshot,
    GateConfig,
    should_compress,
)
from praxis.kernel.compression.caveman.models import ContentType, Dialect, Intensity
from praxis.kernel.compression.caveman.validate import (
    validate_all,
    validate_semantic,
    validate_structural,
)


# ---------------------------------------------------------------------------
# Content boundary detection
# ---------------------------------------------------------------------------

class TestBoundaryDetection:
    def test_pure_prose(self, long_prose_text):
        ct = classify_content(long_prose_text)
        assert ct == ContentType.PROSE_DOMINANT

    def test_code_dominant(self):
        code_heavy = (
            "Here is the code:\n"
            "```python\n" + "x = 1\nprint(x)\n" * 100 + "```\n"
            "End.\n"
        )
        ct = classify_content(code_heavy)
        assert ct == ContentType.CODE_DOMINANT

    def test_empty_string(self):
        assert classify_content("") == ContentType.PROSE_DOMINANT

    def test_extract_code_blocks(self):
        text = "Before\n```python\nprint('hello')\n```\nAfter"
        blocks = extract_code_blocks(text)
        assert len(blocks) == 1
        assert "print" in blocks[0]

    def test_extract_urls(self):
        text = "See https://example.com/path for details and http://other.org too."
        urls = extract_urls(text)
        assert "https://example.com/path" in urls
        assert "http://other.org" in urls

    def test_extract_paths(self):
        text = "File at /usr/local/bin/python and C:\\Windows\\System32\\cmd.exe."
        paths = extract_paths(text)
        assert any("/usr/local/bin/python" in p for p in paths)

    def test_mixed_content(self):
        # Code block is ~15% of the total — below CODE_DOMINANT threshold (30%)
        prose = "Some prose here. " * 10  # ~170 chars of prose
        text = prose + "```python\ncode\n```\n" + prose
        ct = classify_content(text)
        # Small code block in mostly prose → MIXED or PROSE_DOMINANT
        assert ct in (ContentType.PROSE_DOMINANT, ContentType.MIXED)


# ---------------------------------------------------------------------------
# Structural validator
# ---------------------------------------------------------------------------

class TestStructuralValidator:
    def test_passes_identical(self):
        text = "# Title\nSome prose.\n## Section\nMore prose."
        errors = validate_structural(text, text)
        assert errors == []

    def test_heading_count_mismatch(self):
        original = "# Title\n## Subtitle\nContent."
        compressed = "# Title\nContent."
        errors = validate_structural(original, compressed)
        kinds = [e.kind for e in errors]
        assert "heading_count_mismatch" in kinds

    def test_code_block_corruption(self):
        original = "Text\n```python\nprint('hi')\n```\nEnd"
        compressed = "Text\n```python\nprint('modified')\n```\nEnd"
        errors = validate_structural(original, compressed)
        kinds = [e.kind for e in errors]
        assert "code_block_corruption" in kinds

    def test_code_block_preserved(self):
        code = "```python\nprint('hi')\n```"
        original = f"Text\n{code}\nEnd"
        compressed = f"Text compressed\n{code}\nEnd"
        errors = validate_structural(original, compressed)
        kinds = [e.kind for e in errors]
        assert "code_block_corruption" not in kinds

    def test_url_drift(self):
        original = "See https://example.com for details."
        compressed = "Details at https://other.com."
        errors = validate_structural(original, compressed)
        kinds = [e.kind for e in errors]
        assert "url_drift" in kinds

    def test_url_preserved(self):
        url = "https://example.com/path"
        original = f"See {url} for info."
        compressed = f"Info: {url}"
        errors = validate_structural(original, compressed)
        kinds = [e.kind for e in errors]
        assert "url_drift" not in kinds

    def test_bullet_drift(self):
        original = "\n".join(f"- Item {i}" for i in range(20))
        compressed = "\n".join(f"- Item {i}" for i in range(5))  # dramatic drop
        errors = validate_structural(original, compressed)
        kinds = [e.kind for e in errors]
        assert "bullet_count_drift" in kinds

    def test_no_bullet_drift_when_original_has_no_bullets(self):
        original = "No bullets here."
        compressed = "Short."
        errors = validate_structural(original, compressed)
        kinds = [e.kind for e in errors]
        assert "bullet_count_drift" not in kinds


# ---------------------------------------------------------------------------
# Semantic validator (S1-S4)
# ---------------------------------------------------------------------------

class TestSemanticValidator:
    def test_passes_identical(self, long_prose_text):
        errors = validate_semantic(long_prose_text, long_prose_text)
        assert errors == []

    def test_s1_negation_drift(self):
        original = "Do not disable this feature. Never remove the safety checks."
        compressed = "Disable this feature. Remove safety checks."  # stripped negations
        errors = validate_semantic(original, compressed)
        kinds = [e.kind for e in errors]
        assert "negation_drift" in kinds

    def test_s2_number_loss(self):
        original = "The value is 42 and the limit is 100."
        compressed = "The value and limit are set."  # numbers dropped
        errors = validate_semantic(original, compressed)
        kinds = [e.kind for e in errors]
        assert "number_loss" in kinds

    def test_s2_numbers_preserved(self):
        original = "The count is 5."
        compressed = "Count: 5."
        errors = validate_semantic(original, compressed)
        kinds = [e.kind for e in errors]
        assert "number_loss" not in kinds

    def test_s3_polarity_flip(self):
        # Original: "safe" dominates → compressed: "unsafe" dominates
        original = "The system is safe, trusted, and supported."
        compressed = "The system is unsafe, untrusted, and unsupported."
        errors = validate_semantic(original, compressed)
        kinds = [e.kind for e in errors]
        assert "polarity_flip" in kinds

    def test_s3_polarity_preserved(self):
        original = "The feature is safe and recommended."
        compressed = "Feature is safe, recommended."
        errors = validate_semantic(original, compressed)
        kinds = [e.kind for e in errors]
        assert "polarity_flip" not in kinds

    def test_s4_imperative_drift(self):
        original = "Use the new API. Run the migration. Include all tests."
        compressed = "Avoid the new API. Skip migration. Omit tests."
        errors = validate_semantic(original, compressed)
        kinds = [e.kind for e in errors]
        assert "imperative_drift" in kinds

    def test_validate_all_combines(self, long_prose_text):
        report = validate_all(long_prose_text, long_prose_text)
        assert report.passed is True
        assert report.structural_errors == []
        assert report.semantic_errors == []


# ---------------------------------------------------------------------------
# Net-positive gate
# ---------------------------------------------------------------------------

class TestGate:
    def _make_fresh_calibration(self) -> CalibrationSnapshot:
        """Calibration that was just refreshed (age ~0s)."""
        return CalibrationSnapshot()

    def test_gate_denies_short_text(self):
        cfg = GateConfig(min_tokens=500)
        cal = self._make_fresh_calibration()
        ok, reason = should_compress(
            "short", Dialect.CAVEMAN_ENGLISH, 5, False, config=cfg, calibration=cal
        )
        assert ok is False
        assert "below_min_length" in reason

    def test_gate_denies_code_dominant(self):
        code_text = "```python\n" + ("x = 1\nprint(x)\n" * 200) + "```"
        cfg = GateConfig(min_tokens=10)  # low floor
        cal = self._make_fresh_calibration()
        ok, reason = should_compress(
            code_text, Dialect.CAVEMAN_ENGLISH, 100, False, config=cfg, calibration=cal
        )
        assert ok is False
        assert "content_type" in reason

    def test_gate_denies_below_break_even(self, long_prose_text):
        cfg = GateConfig(min_tokens=10, break_even_reads=3)
        cal = CalibrationSnapshot(
            savings_per_read_tokens=100.0,
            compression_cost_tokens=400.0,  # needs 4 reads
        )
        ok, reason = should_compress(
            long_prose_text, Dialect.CAVEMAN_ENGLISH, 1, False, config=cfg, calibration=cal
        )
        assert ok is False
        assert "break_even" in reason

    def test_gate_approves_sufficient_reads(self, long_prose_text):
        cfg = GateConfig(min_tokens=10, break_even_reads=3)
        cal = CalibrationSnapshot(
            savings_per_read_tokens=200.0,
            compression_cost_tokens=100.0,  # break_even = 0.5, so 5 reads is plenty
        )
        ok, reason = should_compress(
            long_prose_text, Dialect.CAVEMAN_ENGLISH, 5, False, config=cfg, calibration=cal
        )
        assert ok is True
        assert reason == "ok"

    def test_gate_denies_stale_calibration(self, long_prose_text):
        from datetime import timedelta
        cfg = GateConfig(max_calibration_age_seconds=3600)
        stale_time = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ) - timedelta(days=10)
        cal = CalibrationSnapshot(refreshed_at=stale_time)
        ok, reason = should_compress(
            long_prose_text, Dialect.CAVEMAN_ENGLISH, 10, False, config=cfg, calibration=cal
        )
        assert ok is False
        assert "stale" in reason

    def test_gate_denies_wenyan_not_accepted(self, long_prose_text):
        cfg = GateConfig(min_tokens=10, break_even_reads=1)
        cal = CalibrationSnapshot(savings_per_read_tokens=500.0, compression_cost_tokens=10.0)
        ok, reason = should_compress(
            long_prose_text, Dialect.WENYAN, 10, accept_wenyan=False,
            config=cfg, calibration=cal,
        )
        assert ok is False
        assert "wenyan" in reason

    def test_gate_allows_wenyan_when_accepted(self, long_prose_text):
        cfg = GateConfig(min_tokens=10, break_even_reads=1)
        cal = CalibrationSnapshot(savings_per_read_tokens=500.0, compression_cost_tokens=10.0)
        ok, reason = should_compress(
            long_prose_text, Dialect.WENYAN, 10, accept_wenyan=True,
            config=cfg, calibration=cal,
        )
        assert ok is True
