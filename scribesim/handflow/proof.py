"""Proof primitives and validation helpers for TD-014 handflow."""

from __future__ import annotations

import math
from pathlib import Path

from scribesim.hand.profile import HandProfile
from scribesim.handvalidate import StageReport, evaluate_gate, write_stage_report
from scribesim.pathguide import DensePathGuide, guide_from_waypoints

from .controller import GuidedHandFlowController
from .render import render_trajectory_proof


def build_primitive_proof_guides(*, x_height_mm: float = 3.5) -> dict[str, DensePathGuide]:
    """Create the first primitive proof set for controller bring-up."""

    return {
        "downstroke": guide_from_waypoints(
            "downstroke",
            [(0.20, 0.10, True), (0.20, 1.05, True)],
            x_height_mm=x_height_mm,
            x_advance_xh=0.35,
            kind="glyph",
            source_id="primitive-proof:downstroke",
            source_path="scribesim/handflow/proof.py",
            split="validation",
            source_resolution_ppmm=16.0,
        ),
        "upstroke": guide_from_waypoints(
            "upstroke",
            [(0.10, 0.95, True), (0.45, 0.20, True)],
            x_height_mm=x_height_mm,
            x_advance_xh=0.50,
            kind="glyph",
            default_pressure=0.28,
            corridor_half_width_mm=0.14,
            source_id="primitive-proof:upstroke",
            source_path="scribesim/handflow/proof.py",
            split="validation",
            source_resolution_ppmm=16.0,
        ),
        "bowl_arc": guide_from_waypoints(
            "bowl_arc",
            [(0.12, 0.78, True), (0.28, 0.44, True), (0.48, 0.30, True), (0.66, 0.46, True), (0.72, 0.82, True)],
            x_height_mm=x_height_mm,
            x_advance_xh=0.82,
            kind="glyph",
            source_id="primitive-proof:bowl_arc",
            source_path="scribesim/handflow/proof.py",
            split="validation",
            source_resolution_ppmm=16.0,
        ),
        "ascender_loop": guide_from_waypoints(
            "ascender_loop",
            [
                (0.34, 1.18, True),
                (0.42, 0.80, True),
                (0.46, 0.28, True),
                (0.40, -0.18, True),
                (0.28, 0.10, True),
                (0.26, 0.62, True),
                (0.34, 1.04, True),
            ],
            x_height_mm=x_height_mm,
            x_advance_xh=0.72,
            kind="glyph",
            source_id="primitive-proof:ascender_loop",
            source_path="scribesim/handflow/proof.py",
            split="validation",
            source_resolution_ppmm=16.0,
        ),
        "pen_lift": guide_from_waypoints(
            "pen_lift",
            [(0.10, 0.95, True), (0.10, 0.70, True), (0.10, 0.70, False), (0.16, 0.52, False), (0.38, 0.42, False)],
            x_height_mm=x_height_mm,
            x_advance_xh=0.46,
            kind="glyph",
            corridor_half_width_mm=0.12,
            source_id="primitive-proof:pen_lift",
            source_path="scribesim/handflow/proof.py",
            split="validation",
            source_resolution_ppmm=16.0,
        ),
        "minim_pair": guide_from_waypoints(
            "minim_pair",
            [
                (0.12, 0.08, True),
                (0.12, 1.02, True),
                (0.38, 0.18, True),
                (0.62, 1.02, True),
            ],
            x_height_mm=x_height_mm,
            x_advance_xh=0.75,
            kind="glyph",
            source_id="primitive-proof:minim_pair",
            source_path="scribesim/handflow/proof.py",
            split="validation",
            source_resolution_ppmm=16.0,
        ),
    }


def run_primitive_proof(
    output_dir: Path | str,
    *,
    profile: HandProfile,
    guides: dict[str, DensePathGuide] | None = None,
    dpi: int = 300,
    supersample: int = 3,
    dt: float = 0.002,
) -> dict[str, StageReport]:
    """Render proof primitives and emit Level 0 reports."""

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    controller = GuidedHandFlowController(profile)
    from scribesim.render.nib import PhysicsNib, mark_width
    reports: dict[str, StageReport] = {}

    from scribesim.handvalidate import (
        contact_accuracy,
        corridor_containment_ratio,
        self_intersection_count,
        width_profile_error,
    )

    active_guides = guides or build_primitive_proof_guides(x_height_mm=profile.letterform.x_height_mm)
    pnib = PhysicsNib(
        width_mm=profile.nib.width_mm,
        angle_deg=profile.nib.angle_deg,
        flexibility=profile.nib.flexibility,
        cut_quality=profile.nib.cut_quality,
        attack_pressure_multiplier=profile.nib.attack_pressure_multiplier,
        release_taper_length=profile.nib.release_taper_length,
    )

    for name, guide in active_guides.items():
        result = controller.simulate_guide(guide, dt=dt)
        render_trajectory_proof(
            result.trajectory,
            profile=profile,
            output_path=output_root / f"{name}.png",
            dpi=dpi,
            supersample=supersample,
        )
        expected_widths = []
        aligned_contact = [sample for sample in result.guide_aligned_trajectory if sample.contact]
        for idx, sample in enumerate(aligned_contact):
            if not sample.contact:
                continue
            direction_deg = 0.0
            if len(aligned_contact) >= 2:
                if idx == 0:
                    a = aligned_contact[0]
                    b = aligned_contact[1]
                elif idx >= len(aligned_contact) - 1:
                    a = aligned_contact[-2]
                    b = aligned_contact[-1]
                else:
                    a = aligned_contact[idx - 1]
                    b = aligned_contact[idx + 1]
                direction_deg = math.degrees(math.atan2(b.y_mm - a.y_mm, b.x_mm - a.x_mm))
            expected_widths.append(
                mark_width(
                    pnib,
                    direction_deg=direction_deg,
                    pressure=sample.pressure or 0.0,
                    t=idx / max(len(aligned_contact) - 1, 1),
                )
            )
        metrics = {
            "corridor_containment": corridor_containment_ratio(result.guide_aligned_trajectory, guide),
            "self_intersections": float(self_intersection_count(result.trajectory)),
            "contact_accuracy": contact_accuracy(result.guide_aligned_trajectory, guide),
            "width_profile_error": width_profile_error(
                [sample.width_mm for sample in result.guide_aligned_trajectory if sample.contact],
                expected_widths,
            ),
        }
        gate = evaluate_gate("primitive", metrics)
        report = StageReport(
            stage=f"primitive:{name}",
            metrics=metrics,
            gate=gate,
            notes=(f"supersample={supersample}", f"out_of_corridor_steps={result.out_of_corridor_steps}"),
        )
        write_stage_report(report, output_root)
        reports[name] = report

    return reports
