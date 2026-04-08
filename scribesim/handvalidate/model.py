"""Data structures for TD-014 hand validation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TrajectorySample:
    """One observed writing sample in physical coordinates."""

    x_mm: float
    y_mm: float
    contact: bool = True
    width_mm: float | None = None
    pressure: float | None = None
    nib_angle_deg: float | None = None


@dataclass(frozen=True)
class GateRule:
    """One metric rule loaded from config."""

    metric: str
    op: str
    threshold: float
    required: bool = True
    description: str | None = None


@dataclass(frozen=True)
class StageGate:
    """Gate definition for one curriculum stage."""

    stage: str
    label: str
    rules: tuple[GateRule, ...]


@dataclass(frozen=True)
class GateFailure:
    """One failed or missing rule evaluation."""

    metric: str
    reason: str
    actual: float | None = None
    op: str | None = None
    threshold: float | None = None
    required: bool = True


@dataclass(frozen=True)
class GateDecision:
    """Pass/fail result for a stage gate."""

    stage: str
    passed: bool
    failures: tuple[GateFailure, ...] = field(default_factory=tuple)
    advisories: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DatasetPolicy:
    """Dataset admission policy for promotion or exploratory runs."""

    name: str
    allowed_confidence_tiers: tuple[str, ...]
    require_provenance: bool = True
    require_resolution_metadata: bool = True
    min_heldout_symbol_coverage: float = 0.0


@dataclass(frozen=True)
class DatasetPolicyDecision:
    """Pass/fail result for dataset policy checks."""

    name: str
    passed: bool
    reasons: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class StageReport:
    """Structured output for one validation run."""

    stage: str
    metrics: dict[str, float]
    gate: GateDecision
    dataset_policy: str | None = None
    dataset_policy_passed: bool | None = None
    dataset_policy_reasons: tuple[str, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class FolioBenchCase:
    """One representative folio slice used in the rollout bench."""

    name: str
    folio_id: str
    folio_path: str
    description: str = ""
    line_limit: int | None = None
    profile_overrides: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class FolioBenchManifest:
    """Committed manifest for TD-014 folio A/B rollout validation."""

    stage_id: str
    checkpoint_id: str
    word_line_manifest_path: str
    word_line_candidate_name: str
    weather_profile_path: str
    guided_supersample: int = 4
    proof_dpi: int = 220
    proof_supersample: int = 3
    dt: float = 0.002
    evo_quality: str = "balanced"
    evo_evolve: bool = True
    base_profile_overrides: dict[str, object] = field(default_factory=dict)
    cases: tuple[FolioBenchCase, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class FolioPromotionDecision:
    """Explicit stop/go decision for guided folio promotion."""

    checkpoint_id: str
    promotable: bool
    reasons: tuple[str, ...] = field(default_factory=tuple)
    winning_cases: tuple[str, ...] = field(default_factory=tuple)
    summary_metrics: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class FolioBenchRunResult:
    """Result summary for a folio regression bench run."""

    passed: bool
    manifest: FolioBenchManifest
    decision: FolioPromotionDecision
    output_dir: str
