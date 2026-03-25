"""TD-014 curriculum orchestration."""

from scribesim.curriculum.model import (
    GlyphJoinCandidate,
    GlyphJoinCheckpoint,
    GlyphJoinManifest,
    GlyphJoinRunResult,
    PrimitiveCandidate,
    PrimitiveCheckpoint,
    PrimitiveManifest,
    PrimitiveRunResult,
    WordLineCandidate,
    WordLineCheckpoint,
    WordLineManifest,
    WordLineRunResult,
)
from scribesim.curriculum.glyph_join import (
    DEFAULT_GLYPH_JOIN_DATASET_SUMMARY_PATH,
    DEFAULT_GLYPH_JOIN_MANIFEST_PATH,
    load_glyph_join_manifest,
    run_glyph_join_curriculum,
)
from scribesim.curriculum.primitive import (
    DEFAULT_DATASET_SUMMARY_PATH,
    DEFAULT_PRIMITIVE_MANIFEST_PATH,
    load_primitive_manifest,
    run_primitive_curriculum,
)
from scribesim.curriculum.word_line import (
    DEFAULT_WORD_LINE_DATASET_SUMMARY_PATH,
    DEFAULT_WORD_LINE_MANIFEST_PATH,
    load_word_line_manifest,
    run_word_line_curriculum,
)

__all__ = [
    "DEFAULT_DATASET_SUMMARY_PATH",
    "DEFAULT_GLYPH_JOIN_DATASET_SUMMARY_PATH",
    "DEFAULT_GLYPH_JOIN_MANIFEST_PATH",
    "DEFAULT_PRIMITIVE_MANIFEST_PATH",
    "GlyphJoinCandidate",
    "GlyphJoinCheckpoint",
    "GlyphJoinManifest",
    "GlyphJoinRunResult",
    "PrimitiveCandidate",
    "PrimitiveCheckpoint",
    "PrimitiveManifest",
    "PrimitiveRunResult",
    "WordLineCandidate",
    "WordLineCheckpoint",
    "WordLineManifest",
    "WordLineRunResult",
    "load_glyph_join_manifest",
    "load_primitive_manifest",
    "load_word_line_manifest",
    "run_glyph_join_curriculum",
    "run_primitive_curriculum",
    "run_word_line_curriculum",
    "DEFAULT_WORD_LINE_DATASET_SUMMARY_PATH",
    "DEFAULT_WORD_LINE_MANIFEST_PATH",
]
