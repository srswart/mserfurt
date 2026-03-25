"""TD-014 guided handflow controller and proof renderer."""

from scribesim.handflow.controller import GuidedHandFlowController
from scribesim.handflow.folio import render_guided_folio_lines, simulate_guided_folio_lines
from scribesim.handflow.model import (
    GuidedFolioLineStatus,
    GuidedFolioResolutionError,
    GuidedFolioSimulation,
    HandStateV2,
    SessionGuide,
    SessionResult,
    SessionWordGuide,
    SimulationResult,
    StateTraceEntry,
    TrackPlan,
    TrackPlanSample,
)
from scribesim.handflow.planning import build_track_plan, sample_plan
from scribesim.handflow.proof import build_primitive_proof_guides, run_primitive_proof
from scribesim.handflow.render import render_trajectory_canvas, render_trajectory_proof
from scribesim.handflow.session import (
    PROOF_WORDS,
    build_line_session,
    build_proof_vocabulary_session,
    build_word_session,
    load_word_guide_catalog,
    run_stateful_word_proof,
)

__all__ = [
    "GuidedHandFlowController",
    "GuidedFolioLineStatus",
    "GuidedFolioResolutionError",
    "GuidedFolioSimulation",
    "HandStateV2",
    "PROOF_WORDS",
    "SessionGuide",
    "SessionResult",
    "SessionWordGuide",
    "SimulationResult",
    "StateTraceEntry",
    "TrackPlan",
    "TrackPlanSample",
    "build_line_session",
    "build_primitive_proof_guides",
    "build_proof_vocabulary_session",
    "build_track_plan",
    "build_word_session",
    "load_word_guide_catalog",
    "render_guided_folio_lines",
    "render_trajectory_canvas",
    "render_trajectory_proof",
    "run_primitive_proof",
    "run_stateful_word_proof",
    "sample_plan",
    "simulate_guided_folio_lines",
]
