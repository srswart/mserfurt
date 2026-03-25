"""Data structures for TD-014 curriculum promotion."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PrimitiveCandidate:
    """One candidate profile configuration to evaluate."""

    name: str
    description: str = ""
    profile_overrides: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class PrimitiveManifest:
    """Committed manifest for Level 0 primitive promotion."""

    stage_id: str
    checkpoint_id: str
    dataset_policy: str
    exercises: tuple[str, ...]
    proof_dpi: int
    proof_supersample: int
    dt: float
    base_profile_overrides: dict[str, object] = field(default_factory=dict)
    candidates: tuple[PrimitiveCandidate, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PrimitiveCheckpoint:
    """Frozen metadata for a promoted primitive checkpoint."""

    checkpoint_id: str
    candidate_name: str
    manifest_path: str
    dataset_policy: str
    passed: bool
    exercise_names: tuple[str, ...]
    profile_flat: dict[str, object]


@dataclass(frozen=True)
class PrimitiveRunResult:
    """Result summary for a primitive curriculum run."""

    passed: bool
    manifest: PrimitiveManifest
    selected_candidate: str | None
    checkpoint_path: str | None
    output_dir: str


@dataclass(frozen=True)
class GlyphJoinCandidate:
    """One candidate profile configuration for glyph/join promotion."""

    name: str
    description: str = ""
    profile_overrides: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class GlyphJoinManifest:
    """Committed manifest for Level 1 glyph/join promotion."""

    stage_id: str
    checkpoint_id: str
    dataset_policy: str
    primitive_manifest_path: str
    primitive_candidate_name: str
    training_glyphs: tuple[str, ...]
    promotion_glyphs: tuple[str, ...]
    training_joins: tuple[str, ...]
    promotion_joins: tuple[str, ...]
    proof_dpi: int
    proof_supersample: int
    dt: float
    base_profile_overrides: dict[str, object] = field(default_factory=dict)
    candidates: tuple[GlyphJoinCandidate, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class GlyphJoinCheckpoint:
    """Frozen metadata for a promoted glyph/join checkpoint."""

    checkpoint_id: str
    candidate_name: str
    manifest_path: str
    primitive_manifest_path: str
    primitive_candidate_name: str
    dataset_policy: str
    passed: bool
    promotion_glyphs: tuple[str, ...]
    promotion_joins: tuple[str, ...]
    profile_flat: dict[str, object]


@dataclass(frozen=True)
class GlyphJoinRunResult:
    """Result summary for a glyph/join curriculum run."""

    passed: bool
    manifest: GlyphJoinManifest
    selected_candidate: str | None
    checkpoint_path: str | None
    output_dir: str


@dataclass(frozen=True)
class WordLineCandidate:
    """One candidate profile configuration for word/line promotion."""

    name: str
    description: str = ""
    profile_overrides: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class WordLineManifest:
    """Committed manifest for Level 2 word/line promotion."""

    stage_id: str
    checkpoint_id: str
    dataset_policy: str
    glyph_join_manifest_path: str
    glyph_join_candidate_name: str
    proof_entries: tuple[str, ...]
    training_lines: tuple[str, ...]
    promotion_lines: tuple[str, ...]
    proof_dpi: int
    proof_supersample: int
    dt: float
    base_profile_overrides: dict[str, object] = field(default_factory=dict)
    candidates: tuple[WordLineCandidate, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class WordLineCheckpoint:
    """Frozen metadata for a promoted word/line checkpoint."""

    checkpoint_id: str
    candidate_name: str
    manifest_path: str
    glyph_join_manifest_path: str
    glyph_join_candidate_name: str
    dataset_policy: str
    passed: bool
    proof_entries: tuple[str, ...]
    promotion_lines: tuple[str, ...]
    profile_flat: dict[str, object]


@dataclass(frozen=True)
class WordLineRunResult:
    """Result summary for a word/line curriculum run."""

    passed: bool
    manifest: WordLineManifest
    selected_candidate: str | None
    checkpoint_path: str | None
    output_dir: str
