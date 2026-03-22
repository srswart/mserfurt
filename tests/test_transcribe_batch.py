"""Tests for scribesim/transcribe/ — ADV-SS-TRANSCRIBE-001 (red phase)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_png(path: Path, h: int = 20, w: int = 40) -> Path:
    """Write a tiny grayscale PNG for testing."""
    arr = np.full((h, w), 200, dtype=np.uint8)
    arr[5:15, 10:30] = 30
    Image.fromarray(arr).save(path, format="PNG")
    return path


# ---------------------------------------------------------------------------
# clean_response tests
# ---------------------------------------------------------------------------

class TestCleanResponse:
    def test_strips_reasoning_bleed_through(self):
        """Multi-line response with reasoning → only first clean line kept; if it looks like
        reasoning, return '?'."""
        from scribesim.transcribe.batch import clean_response
        raw = "let me look at this carefully\nder"
        assert clean_response(raw) == "?"

    def test_soft_prefix_preserved(self):
        """~word soft-confidence prefix must survive cleaning."""
        from scribesim.transcribe.batch import clean_response
        assert clean_response("~der") == "~der"

    def test_plain_word(self):
        """Simple word without prefix → returned as-is."""
        from scribesim.transcribe.batch import clean_response
        assert clean_response("  die  ") == "die"

    def test_unknown_returns_question_mark(self):
        """Empty or whitespace-only response → '?'."""
        from scribesim.transcribe.batch import clean_response
        assert clean_response("   ") == "?"

    def test_too_long_returns_question_mark(self):
        """Strings over 20 chars are likely reasoning bleed-through → '?'."""
        from scribesim.transcribe.batch import clean_response
        assert clean_response("this is way too long to be a word") == "?"

    def test_strips_non_alpha(self):
        """Punctuation and digits stripped (but ~ soft prefix kept if leading)."""
        from scribesim.transcribe.batch import clean_response
        assert clean_response("w0rd!") == "wrd"


# ---------------------------------------------------------------------------
# build_few_shot_content tests
# ---------------------------------------------------------------------------

class TestBuildFewShotContent:
    def test_image_count(self, tmp_path):
        """N examples → 2N content blocks (one image + one text each)."""
        from scribesim.transcribe.examples import build_few_shot_content
        examples = []
        for i in range(4):
            p = _write_png(tmp_path / f"ex{i}.png")
            examples.append({"image_path": p, "transcription": f"word{i}"})
        blocks = build_few_shot_content(examples)
        assert len(blocks) == 8  # 4 image + 4 text

    def test_alternating_image_text(self, tmp_path):
        """Content blocks alternate image → text."""
        from scribesim.transcribe.examples import build_few_shot_content
        p = _write_png(tmp_path / "ex.png")
        examples = [{"image_path": p, "transcription": "die"}]
        blocks = build_few_shot_content(examples)
        assert blocks[0]["type"] == "image"
        assert blocks[1]["type"] == "text"
        assert "die" in blocks[1]["text"]

    def test_empty_examples(self):
        """Empty examples list → empty content blocks."""
        from scribesim.transcribe.examples import build_few_shot_content
        assert build_few_shot_content([]) == []


# ---------------------------------------------------------------------------
# retry_unknowns tests
# ---------------------------------------------------------------------------

class TestRetryUnknowns:
    def test_merges_results(self, tmp_path):
        """Known results preserved; '?' entries replaced by retry output."""
        from scribesim.transcribe.batch import retry_unknowns
        crops = [tmp_path / f"w{i}.png" for i in range(3)]
        for c in crops:
            _write_png(c)
        # w0 and w2 are unknowns; w1 is known
        initial = {crops[0].stem: "?", crops[1].stem: "die", crops[2].stem: "?"}

        # Mock client that returns "~gut" for all retry requests
        mock_client = MagicMock()
        mock_batch = MagicMock()
        mock_batch.id = "batch_retry_001"
        mock_batch.processing_status = "ended"
        mock_batch.request_counts = MagicMock(processing=0, succeeded=2, errored=0)
        mock_client.messages.batches.create.return_value = mock_batch
        mock_client.messages.batches.retrieve.return_value = mock_batch

        def _mock_results(batch_id):
            for stem in [crops[0].stem, crops[2].stem]:
                r = MagicMock()
                r.custom_id = stem
                r.result.type = "succeeded"
                r.result.message.content = [MagicMock(type="text", text="~gut")]
                yield r

        mock_client.messages.batches.results.side_effect = _mock_results

        merged = retry_unknowns(
            unknowns={crops[0].stem: crops[0], crops[2].stem: crops[2]},
            initial_results=initial,
            client=mock_client,
            model="claude-haiku-4-5-20251001",
            examples=[],
        )
        assert merged[crops[0].stem] == "~gut"
        assert merged[crops[1].stem] == "die"  # preserved
        assert merged[crops[2].stem] == "~gut"

    def test_known_results_unchanged(self, tmp_path):
        """When unknowns is empty, initial_results returned unchanged."""
        from scribesim.transcribe.batch import retry_unknowns
        initial = {"w0": "die", "w1": "und"}
        merged = retry_unknowns(
            unknowns={},
            initial_results=initial,
            client=MagicMock(),
            model="claude-haiku-4-5-20251001",
            examples=[],
        )
        assert merged == initial


# ---------------------------------------------------------------------------
# extract-letters tilde stripping
# ---------------------------------------------------------------------------

class TestExtractLettersTildeStripping:
    def test_tilde_stripped_before_labeling(self, tmp_path):
        """'~der' in transcription produces same letter labels as 'der' — tilde is stripped."""
        from click.testing import CliRunner
        from scribesim.cli import main

        # Three distinct letter-like blobs in a 40x90 image (pattern from test_segment.py)
        word_img = np.full((40, 90), 255, dtype=np.uint8)
        word_img[5:35, 2:18] = 0    # blob 1  (16px wide, 30px tall)
        word_img[5:35, 35:55] = 0   # blob 2  (20px wide)
        word_img[5:35, 72:88] = 0   # blob 3  (16px wide)
        Image.fromarray(word_img).save(tmp_path / "w0001.png")

        # Write transcription with tilde-prefixed word
        trans = tmp_path / "transcription.txt"
        trans.write_text("~der\n")

        out_dir = tmp_path / "letters"
        runner = CliRunner()
        result = runner.invoke(main, [
            "extract-letters",
            "--words", str(tmp_path),
            "--output", str(out_dir),
            "--transcription", str(trans),
        ])
        assert result.exit_code == 0, result.output

        # The key assertion: no '~der' directory must exist (tilde not stripped = bug)
        assert not (out_dir / "~der").exists(), "'~der' directory created — tilde not stripped"
        # Also confirm no directory starting with '~' was created
        if out_dir.exists():
            tilde_dirs = [d for d in out_dir.iterdir() if d.is_dir() and d.name.startswith("~")]
            assert tilde_dirs == [], f"Tilde directories created: {tilde_dirs}"
