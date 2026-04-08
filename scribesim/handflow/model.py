"""Core data structures for TD-014 guided handflow."""

from __future__ import annotations

from dataclasses import dataclass, field

from scribesim.pathguide import DensePathGuide
from scribesim.handvalidate import TrajectorySample


@dataclass(frozen=True)
class TrackPlanSample:
    """Desired controller state at one point along a planned guide."""

    t_s: float
    arc_length_mm: float
    x_mm: float
    y_mm: float
    vx_mm_s: float
    vy_mm_s: float
    speed_mm_s: float
    pressure: float
    nib_angle_deg: float
    contact: bool
    corridor_half_width_mm: float
    progress_ratio: float = 0.0


@dataclass(frozen=True)
class TrackPlan:
    """Dense desired state sequence derived from a path guide."""

    guide_symbol: str
    samples: tuple[TrackPlanSample, ...]
    x_height_mm: float
    x_advance_mm: float

    @property
    def total_time_s(self) -> float:
        if not self.samples:
            return 0.0
        return self.samples[-1].t_s

    @property
    def total_length_mm(self) -> float:
        if not self.samples:
            return 0.0
        return self.samples[-1].arc_length_mm


@dataclass
class HandStateV2:
    """Persistent guided-hand controller state."""

    pos_x_mm: float
    pos_y_mm: float
    vel_x_mm_s: float = 0.0
    vel_y_mm_s: float = 0.0
    acc_x_mm_s2: float = 0.0
    acc_y_mm_s2: float = 0.0
    nib_contact: bool = False
    nib_pressure: float = 0.5
    nib_angle_deg: float = 40.0
    ink_reservoir: float = 1.0
    fatigue: float = 0.0
    rhythm_phase: float = 0.0
    time_s: float = 0.0
    trace: list[TrajectorySample] = field(default_factory=list)

    @property
    def speed_mm_s(self) -> float:
        return (self.vel_x_mm_s ** 2 + self.vel_y_mm_s ** 2) ** 0.5


@dataclass(frozen=True)
class SimulationResult:
    """Output from following one guide with the planned-state controller."""

    plan: TrackPlan
    final_state: HandStateV2
    trajectory: tuple[TrajectorySample, ...]
    guide_aligned_trajectory: tuple[TrajectorySample, ...]
    out_of_corridor_steps: int
    max_corridor_error_mm: float


@dataclass(frozen=True)
class SessionGuide:
    """One guide segment in a persistent writing session."""

    symbol: str
    guide: DensePathGuide
    kind: str
    word: str | None = None
    word_index: int | None = None
    requested_symbol: str | None = None
    resolved_symbol: str | None = None
    resolution_kind: str = "exact"
    dip_before: bool = False
    pause_after_s: float = 0.0


@dataclass(frozen=True)
class SessionWordGuide:
    """One merged word guide inside a multi-word session."""

    text: str
    word_index: int
    guide: DensePathGuide


@dataclass(frozen=True)
class StateTraceEntry:
    """Boundary-level state log for persistent guided writing."""

    symbol: str
    kind: str
    word: str | None
    word_index: int | None
    start_time_s: float
    end_time_s: float
    start_speed_mm_s: float
    end_speed_mm_s: float
    start_pressure: float
    end_pressure: float
    start_ink_reservoir: float
    end_ink_reservoir: float
    dip_before: bool = False


@dataclass(frozen=True)
class SessionResult:
    """Output from following a persistent sequence of guides."""

    final_state: HandStateV2
    trajectory: tuple[TrajectorySample, ...]
    guide_aligned_trajectory: tuple[TrajectorySample, ...]
    segments: tuple[SimulationResult, ...]
    state_trace: tuple[StateTraceEntry, ...]


@dataclass(frozen=True)
class GuidedFolioLineStatus:
    """Resolution and renderability status for one folio line."""

    line_index: int
    line_text: str
    glyph_count: int
    exact_character_coverage: float
    alias_substitution_count: int
    normalized_substitution_count: int
    exact_only_passed: bool
    non_exact_symbols: tuple[str, ...] = ()
    resolution_error: str | None = None


@dataclass(frozen=True)
class GuidedFolioSimulation:
    """Simulated folio trajectories plus line-level resolution status."""

    trajectory: tuple[TrajectorySample, ...]
    guide_aligned_trajectory: tuple[TrajectorySample, ...]
    line_statuses: tuple[GuidedFolioLineStatus, ...]
    exact_symbols: bool


class GuidedFolioResolutionError(ValueError):
    """Raised when exact-symbol folio rendering encounters non-exact glyph resolution."""

    def __init__(
        self,
        message: str,
        *,
        line_statuses: tuple[GuidedFolioLineStatus, ...],
    ) -> None:
        super().__init__(message)
        self.line_statuses = line_statuses
